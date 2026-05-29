import datetime

from app.core.config import settings
from app.schemas.investigation import InvestigationState
from app.services.rules_judge_service import _aggregate_correlation_fields
from app.schemas.report import ReportResponse
from app.services.github_query_budget import github_rate_limited_from_context


class ReportGenerator:
    """Produces the final investigation report as a structured payload and markdown."""

    def generate(
        self,
        state: InvestigationState,
        severity_score: float,
        remediation_mode: str,
        citations: list[str],
    ) -> tuple[ReportResponse, str]:
        timeline = self._build_timeline(state)
        seen_suspects: set[str] = set()
        suspects: list[str] = []
        for h in sorted(state.hypotheses, key=lambda hyp: -hyp.confidence):
            text = h.text.strip()
            if not text or text in seen_suspects:
                continue
            seen_suspects.add(text)
            suspects.append(text)
            if len(suspects) >= 5:
                break
        unresolved = self._build_gaps(state)

        rate_limited = state.github_rate_limited or github_rate_limited_from_context(
            state.trigger_context
        )
        report = ReportResponse(
            investigation_id=state.investigation_id,
            timeline=timeline,
            suspects=suspects,
            citations=citations,
            unresolved_gaps=unresolved,
            severity_score=severity_score,
            remediation_mode=remediation_mode,
            root_cause=state.root_cause,
            github_queries_executed=state.github_queries_executed,
            github_queries_max=settings.max_github_queries_per_investigation,
            github_rate_limited=rate_limited,
        )
        markdown = self._build_markdown(report)
        return report, markdown

    # ------------------------------------------------------------------

    def _build_timeline(self, state: InvestigationState) -> list[str]:
        events = []
        for plan in state.query_plans:
            events.append(f"Iteration {plan.iteration + 1}: {plan.rationale}")
        if state.root_cause:
            events.append(f"Root cause identified: {state.root_cause}")
        return events

    def _build_gaps(self, state: InvestigationState) -> list[str]:
        gaps: list[str] = []
        flags = state.escalation_flags
        if flags.get("missing_ownership"):
            gaps.append("Ownership not confirmed — escalation target unknown.")
        if flags.get("conflicting_hypotheses"):
            gaps.append("Multiple conflicting hypotheses — manual review recommended.")
        if not state.root_cause:
            gaps.append("Root cause not finalized — max iterations reached.")
        if state.github_rate_limited or state.trigger_context.get("github_rate_limited"):
            gaps.append(
                "GitHub API rate limited — ownership/PR queries skipped; "
                "retry later or check collaborators in GitHub UI."
            )
        ctx = _aggregate_correlation_fields(state.evidence_rows)
        if (
            ctx.get("deploy_at")
            and ctx.get("error_message")
            and not ctx.get("pr_number")
        ):
            gaps.append(
                "No PR merged after this deploy — likely a deploy or "
                "configuration change (not a post-deploy code merge)."
            )
        return gaps

    def _build_markdown(self, report: ReportResponse) -> str:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "# Reef — Investigation Report",
            f"**ID:** `{report.investigation_id}`  **Generated:** {ts}",
            "",
            "## Root Cause",
            report.root_cause or "_Not determined._",
            "",
            "## Timeline",
        ]
        for event in report.timeline:
            lines.append(f"- {event}")
        lines += ["", "## Top Suspects"]
        for suspect in report.suspects:
            lines.append(f"- {suspect}")
        lines += [
            "",
            "## Severity",
            f"- Score: **{report.severity_score:.2f}**",
            f"- Remediation mode: **{report.remediation_mode}**",
            "",
            "## GitHub API budget",
            f"- Queries used: **{report.github_queries_executed}/{report.github_queries_max}**",
            f"- Rate limited: **{'yes' if report.github_rate_limited else 'no'}**",
            "",
            "## Evidence Citations",
        ]
        for citation in report.citations:
            lines.append(f"- `{citation}`")
        if report.unresolved_gaps:
            lines += ["", "## Unresolved Gaps"]
            for gap in report.unresolved_gaps:
                lines.append(f"- {gap}")
        return "\n".join(lines)
