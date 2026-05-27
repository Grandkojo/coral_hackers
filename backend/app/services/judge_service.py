from app.schemas.investigation import Hypothesis, InvestigationState

_FATAL_SIGNALS = frozenset({"fatal", "error", "exception", "traceback", "typeerror"})
_DEPLOY_SIGNALS = frozenset({"merged_at", "pr_number", "deployment_id", "commit_sha"})


def _confidence_delta(rows: list[dict]) -> float:
    """Score evidence quality to increment confidence."""
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
        error_msg = row.get("error_message") or ""
        pr_number = row.get("pr_number")
        author = row.get("pr_author") or "unknown"
        sentry_id = row.get("sentry_issue_id") or ""
        slack_text = row.get("text") or ""
        oncall = row.get("oncall") or ""

        if pr_title and error_msg:
            hypotheses.append(
                Hypothesis(
                    text=(
                        f"PR #{pr_number} '{pr_title}' by {author} "
                        f"may have introduced: {error_msg[:80]}"
                    ),
                    confidence=0.65,
                    source_refs=[
                        f"sentry://{sentry_id}",
                        f"github://pr/{pr_number}",
                    ],
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


class JudgeService:
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
            state.confidence_score >= 0.6
            and len(state.evidence_rows) >= 1
            and len(strong) >= 1
        )

    def determine_root_cause(self, state: InvestigationState) -> str | None:
        strong = sorted(
            (h for h in state.hypotheses if h.confidence >= 0.5 and h.source_refs),
            key=lambda h: -h.confidence,
        )
        return strong[0].text if strong else None
