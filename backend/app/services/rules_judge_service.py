import re

from app.core.config import settings
from app.schemas.investigation import Hypothesis, InvestigationState

_FATAL_SIGNALS = frozenset({"fatal", "error", "exception", "traceback", "typeerror"})
_MIN_ITER_FOR_STRUCTURED_ROOT_CAUSE = 3

_DPL_ID_RE = re.compile(r"dpl_[a-zA-Z0-9]+", re.IGNORECASE)
_ISO_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_LONG_NUMERIC_ID_RE = re.compile(r"\b\d{6,}\b")
_DEPLOY_SIGNALS = frozenset({"merged_at", "pr_number", "deployment_id", "commit_sha"})


def _confidence_delta(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    all_text = " ".join(
        f"{k} {v}".lower() for row in rows for k, v in row.items()
    )
    delta = 0.05 * min(len(rows), 10)
    if any(sig in all_text for sig in _FATAL_SIGNALS):
        delta += 0.15
    if any(sig in all_text for sig in _DEPLOY_SIGNALS):
        delta += 0.10
    return round(min(delta, 0.40), 3)


def _extract_hypotheses(rows: list[dict], iteration: int) -> list[Hypothesis]:
    hypotheses: list[Hypothesis] = []
    for row in rows[:5]:
        pr_title = row.get("pr_title") or ""
        error_msg = row.get("error_message") or row.get("issue_title") or ""
        pr_number = row.get("pr_number")
        author = row.get("pr_author") or "unknown"
        sentry_id = row.get("sentry_issue_id") or row.get("issue_id") or ""
        deploy_at = row.get("deploy_at") or ""
        slack_text = row.get("text") or ""
        oncall = row.get("oncall") or ""

        if pr_title and author and author != "unknown" and not error_msg:
            hypotheses.append(
                Hypothesis(
                    text=(
                        f"change_author: PR #{pr_number} '{pr_title[:60]}' "
                        f"by {author}"
                    ),
                    confidence=0.55,
                    source_refs=[f"github://pr/{pr_number}"],
                )
            )
        elif pr_title and error_msg and _pr_merged_after_deploy(
            str(row.get("merged_at") or ""), str(deploy_at or "")
        ):
            deploy_hint = f" (deploy {deploy_at})" if deploy_at else ""
            hypotheses.append(
                Hypothesis(
                    text=(
                        f"PR #{pr_number} '{pr_title}' by {author}{deploy_hint} "
                        f"may have introduced: {error_msg[:80]}"
                    ),
                    confidence=0.65,
                    source_refs=[
                        f"sentry://{sentry_id}",
                        f"github://pr/{pr_number}",
                    ],
                )
            )
            if author and author != "unknown":
                hypotheses.append(
                    Hypothesis(
                        text=(
                            f"change_author: PR #{pr_number} '{pr_title[:60]}' "
                            f"by {author}"
                        ),
                        confidence=0.55,
                        source_refs=[f"github://pr/{pr_number}"],
                    )
                )
        elif error_msg and sentry_id and deploy_at:
            hypotheses.append(
                Hypothesis(
                    text=(
                        f"Sentry issue {sentry_id} ({error_msg[:80]}) "
                        f"first seen after deploy at {deploy_at}"
                    ),
                    confidence=0.70,
                    source_refs=[f"sentry://{sentry_id}"],
                )
            )
        elif slack_text:
            hypotheses.append(
                Hypothesis(
                    text=f"Slack[iter={iteration}]: {slack_text[:120]}",
                    confidence=0.30,
                    source_refs=[
                        f"slack://{row.get('channel', '#incidents')}/{row.get('ts', '')}"
                    ],
                )
            )
        elif oncall:
            hypotheses.append(
                Hypothesis(
                    text=(
                        f"owner: team={row.get('team')} oncall={oncall} "
                        f"service={row.get('service', 'unknown')}"
                    ),
                    confidence=0.50,
                    source_refs=[],
                )
            )
    return hypotheses


def _merged_after_first_seen(merged_at: str, first_seen: str) -> bool:
    """ISO-8601 Zulu timestamps compare lexicographically."""
    if not merged_at or not first_seen:
        return False
    return merged_at.strip() > first_seen.strip()


def _pr_merged_after_deploy(merged_at: str, deploy_at: str) -> bool:
    """PR must be merged at or after deploy time to be a regression candidate."""
    if not merged_at or not deploy_at:
        return True
    return merged_at.strip() >= deploy_at.strip()


def _aggregate_correlation_fields(rows: list[dict]) -> dict[str, str]:
    """Merge PR + Sentry fields spread across multiple query result rows."""
    out: dict[str, str] = {}
    pr_keys = ("pr_number", "pr_title", "pr_author", "merged_at")

    for row in rows:
        for key in (
            "error_message",
            "title",
            "sentry_issue_id",
            "issue_id",
            "first_seen",
            "deployment_id",
            "deploy_at",
        ):
            val = row.get(key)
            if val is None or val == "":
                continue
            if key == "title" and out.get("error_message"):
                continue
            if key == "title":
                out.setdefault("error_message", str(val))
            elif key == "issue_id" and not out.get("sentry_issue_id"):
                out["sentry_issue_id"] = str(val)
            else:
                out.setdefault(key, str(val))

    deploy_at = out.get("deploy_at", "")
    best_merged = ""
    for row in rows:
        if not row.get("pr_number"):
            continue
        merged = str(row.get("merged_at") or "")
        row_deploy = str(row.get("deploy_at") or deploy_at)
        if row_deploy and merged and not _pr_merged_after_deploy(merged, row_deploy):
            continue
        if not out.get("pr_number") or merged > best_merged:
            best_merged = merged
            out["pr_number"] = str(row["pr_number"])
            if row.get("pr_title"):
                out["pr_title"] = str(row["pr_title"])
            if row.get("pr_author"):
                out["pr_author"] = str(row["pr_author"])
            out["merged_at"] = merged
    return out


def has_pr_error_correlation(rows: list[dict]) -> bool:
    ctx = _aggregate_correlation_fields(rows)
    return bool(ctx.get("pr_number") and ctx.get("error_message"))


def _service_label(ctx: dict[str, str], trigger_context: dict[str, str] | None) -> str:
    tc = trigger_context or {}
    repo = tc.get("github_repo") or ctx.get("sentry_project", "")
    if repo.endswith("-api"):
        repo = repo[:-4]
    return repo or "the affected service"


def _exception_head(error_msg: str) -> str:
    if ":" in error_msg:
        return error_msg.split(":", 1)[0].strip()
    return ""


def _error_signatures(error_msg: str) -> set[str]:
    """Tokens we expect in a root-cause summary for this Sentry title."""
    lower = error_msg.lower()
    sigs: set[str] = set()

    head = _exception_head(error_msg).lower()
    if head:
        sigs.add(head)

    rules: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
        (("typeerror",), ("typeerror", "type error", "operand", "null", "none", "checkout")),
        (
            ("valueerror", "invalid credential", "credentials"),
            ("valueerror", "value error", "credential", "schema", "auth", "login"),
        ),
        (
            ("authentication", "unauthorized", "401"),
            ("auth", "login", "401", "unauthorized", "credential", "session"),
        ),
        (("forbidden", "403"), ("403", "forbidden", "permission")),
        (("timeout", "timed out"), ("timeout", "timed out", "deadline")),
        (("connection refused", "connectionerror"), ("connection", "network", "refused")),
        (("attributeerror",), ("attributeerror", "attribute")),
        (("keyerror",), ("keyerror", " missing")),
        (("runtimeerror",), ("runtimeerror",)),
        (("fatal", "exception"), ("error", "exception", "failure", "failed")),
    ]
    for needles, tokens in rules:
        if any(n in lower for n in needles):
            sigs.update(tokens)

    if not sigs:
        sigs.update(
            w
            for w in re.findall(r"[a-z]{4,}", lower)
            if w not in {"error", "after", "the", "with", "from"}
        )
    return sigs


def _root_cause_reflects_error(
    root: str,
    error_msg: str,
    evidence_ctx: dict[str, str] | None = None,
) -> bool:
    """Reject summaries that cite the wrong failure mode (e.g. checkout vs auth)."""
    root_lower = root.lower()
    err_lower = error_msg.lower()
    sigs = _error_signatures(error_msg)

    head = _exception_head(error_msg)
    if head:
        h = head.lower()
        head_ok = h in root_lower or h.replace("error", " error") in root_lower
        if not head_ok:
            return False

    if sigs and not any(token in root_lower for token in sigs):
        return False

    auth_evidence = any(
        t in err_lower
        for t in ("auth", "login", "credential", "401", "unauthorized", "valueerror")
    )
    checkout_evidence = "typeerror" in err_lower or "checkout" in err_lower

    checkout_words = ("checkout", "cart", "500", "payment", "amount")
    auth_words = ("auth", "login", "401", "credential", "session", "token", "unauthorized")

    if evidence_ctx and not evidence_ctx.get("pr_number"):
        if re.search(r"\bpr\s*#\s*\d+", root_lower):
            return False

    if auth_evidence and not checkout_evidence:
        if any(w in root_lower for w in checkout_words) and not any(
            w in root_lower for w in auth_words
        ):
            return False

    if checkout_evidence and "typeerror" in err_lower:
        if "500" in root_lower and not any(
            w in root_lower for w in ("typeerror", "type error", "checkout", *checkout_words)
        ):
            return False

    return True


def _summarize_exception(error_msg: str) -> str:
    lower = error_msg.lower()
    if "typeerror" in lower and "nonetype" in lower:
        return (
            "a checkout TypeError when a null amount is combined with a number"
        )
    if "valueerror" in lower or "invalid credential" in lower:
        detail = error_msg.split(":", 1)[-1].strip() if ":" in error_msg else error_msg
        return f"an authentication error ({detail[:90]})"
    if "401" in lower or "unauthorized" in lower:
        return "authentication failures (401 Unauthorized)"
    head = _exception_head(error_msg)
    if head and ":" in error_msg:
        detail = error_msg.split(":", 1)[1].strip()
        return f"a {head} ({detail[:90]})" if detail else f"a {head}"
    return error_msg[:120]


def is_valid_display_root_cause(
    text: str, evidence_ctx: dict[str, str] | None = None
) -> bool:
    """True when LLM root_cause is safe to show (no ids; aligns with Sentry title)."""
    cleaned = text.strip()
    if len(cleaned) < 25:
        return False
    if _DPL_ID_RE.search(cleaned):
        return False
    if _ISO_TIMESTAMP_RE.search(cleaned):
        return False
    if _LONG_NUMERIC_ID_RE.search(cleaned):
        return False

    err = (evidence_ctx or {}).get("error_message", "")
    if err and not _root_cause_reflects_error(cleaned, err, evidence_ctx):
        return False
    return True


def resolve_display_root_cause(
    state: InvestigationState, llm_root: str | None
) -> str | None:
    """Prefer LLM prose when valid; otherwise rules-based display template."""
    ctx = _aggregate_correlation_fields(state.evidence_rows)
    if llm_root and is_valid_display_root_cause(llm_root, ctx):
        return llm_root.strip()

    if state.iteration_count < _MIN_ITER_FOR_STRUCTURED_ROOT_CAUSE:
        return None
    if not ctx.get("error_message"):
        return None
    if not (ctx.get("pr_number") or ctx.get("deployment_id")):
        return None
    return build_display_root_cause(state.evidence_rows, state.trigger_context)


def build_display_root_cause(
    rows: list[dict], trigger_context: dict[str, str] | None = None
) -> str | None:
    """Human-readable root cause for the report (no Sentry/deploy ids)."""
    ctx = _aggregate_correlation_fields(rows)
    error_msg = ctx.get("error_message")
    if not error_msg:
        return None

    service = _service_label(ctx, trigger_context)
    exc = _summarize_exception(error_msg)
    author = ctx.get("pr_author") or ""
    merged_at = ctx.get("merged_at", "")
    first_seen = ctx.get("first_seen", "")
    has_deploy = bool(ctx.get("deployment_id") or ctx.get("deploy_at"))

    deploy_at = ctx.get("deploy_at", "")
    pr_number = ctx.get("pr_number")
    pr_correlated = bool(
        pr_number
        and author
        and author != "unknown"
        and _pr_merged_after_deploy(merged_at, deploy_at)
    )

    if pr_correlated:
        if _merged_after_first_seen(merged_at, first_seen):
            return (
                f"A recent production deploy to {service} exposed {exc}, with "
                f"errors beginning shortly after the deployment. A related pull "
                f"request by {author} merged later and is unlikely to be the "
                f"trigger — deploy or configuration change is the likely cause."
            )
        return (
            f"A recent code change in {service} by {author} likely introduced "
            f"{exc}, correlated with the production deployment and error spike."
        )

    if has_deploy:
        return (
            f"A recent production deploy to {service} exposed {exc}, with errors "
            f"starting shortly after the deployment went live."
        )

    return (
        f"{exc.capitalize()} was detected in {service} during the incident window."
    )


def build_structured_root_cause(rows: list[dict]) -> str | None:
    """Technical root cause (ids + timestamps) — used in tests and markdown detail."""
    ctx = _aggregate_correlation_fields(rows)
    error_msg = ctx.get("error_message")
    pr_number = ctx.get("pr_number")
    if not error_msg or not pr_number:
        return None

    sentry_id = ctx.get("sentry_issue_id", "")
    author = ctx.get("pr_author") or "unknown"
    deploy_id = ctx.get("deployment_id", "")
    deploy_at = ctx.get("deploy_at", "")
    merged_at = ctx.get("merged_at", "")
    first_seen = ctx.get("first_seen", "")

    parts: list[str] = []
    if sentry_id:
        parts.append(f"Sentry issue {sentry_id}: {error_msg}")
    else:
        parts.append(error_msg)

    if deploy_id or deploy_at:
        deploy_bit = deploy_id or "deployment"
        if deploy_at:
            deploy_bit = f"{deploy_bit} at {deploy_at}"
        parts.append(f"first seen after deploy {deploy_bit}")

    if author and author != "unknown":
        pr_bit = f"PR #{pr_number} by {author}"
        if merged_at:
            pr_bit += f" (merged {merged_at})"
        parts.append(pr_bit)

    if _merged_after_first_seen(merged_at, first_seen):
        parts.append(
            "PR merged after first error — deploy/config change is the likely "
            "trigger; PR is time-correlated, not proven code cause"
        )

    return ". ".join(parts) + "."


class RulesJudgeService:
    """Rules-based judge: scores evidence, extracts hypotheses, checks sufficiency."""

    def update_state(self, state: InvestigationState, rows: list[dict]) -> None:
        delta = _confidence_delta(rows)
        state.confidence_score = round(min(1.0, state.confidence_score + delta), 3)
        state.hypotheses.extend(_extract_hypotheses(rows, state.iteration_count))

    def has_sufficient_evidence(self, state: InvestigationState) -> bool:
        strong = [
            h for h in state.hypotheses if h.confidence >= 0.5 and h.source_refs
        ]
        return (
            state.confidence_score >= settings.confidence_threshold
            and len(state.evidence_rows) >= 1
            and len(strong) >= 1
        )

    def determine_structured_root_cause(
        self, state: InvestigationState
    ) -> str | None:
        """Rules-only display template (fallback when LLM root_cause is missing/invalid)."""
        if state.iteration_count < _MIN_ITER_FOR_STRUCTURED_ROOT_CAUSE:
            return None
        ctx = _aggregate_correlation_fields(state.evidence_rows)
        if not ctx.get("error_message"):
            return None
        if not (ctx.get("pr_number") or ctx.get("deployment_id")):
            return None
        return build_display_root_cause(
            state.evidence_rows, state.trigger_context
        )

    def determine_root_cause(self, state: InvestigationState) -> str | None:
        display = self.determine_structured_root_cause(state)
        if display:
            return display
        strong = sorted(
            (h for h in state.hypotheses if h.confidence >= 0.5 and h.source_refs),
            key=lambda h: -h.confidence,
        )
        return strong[0].text if strong else None
