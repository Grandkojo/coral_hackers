import datetime

from app.schemas.investigation import InvestigationState
from app.schemas.report import ReportResponse


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
        suspects = [
            h.text
            for h in sorted(state.hypotheses, key=lambda h: -h.confidence)[:5]
        ]
        unresolved = self._build_gaps(state)

        report = ReportResponse(
            investigation_id=state.investigation_id,
            timeline=timeline,
            suspects=suspects,
            citations=citations,
            unresolved_gaps=unresolved,
            severity_score=severity_score,
            remediation_mode=remediation_mode,
            root_cause=state.root_cause,
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
            "## Evidence Citations",
        ]
        for citation in report.citations:
            lines.append(f"- `{citation}`")
        if report.unresolved_gaps:
            lines += ["", "## Unresolved Gaps"]
            for gap in report.unresolved_gaps:
                lines.append(f"- {gap}")
        return "\n".join(lines)
