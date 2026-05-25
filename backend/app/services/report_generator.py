from app.schemas.investigation import InvestigationState
from app.schemas.report import ReportResponse


class ReportGenerator:
    """Produces the final investigation report payload."""

    def generate(
        self,
        state: InvestigationState,
        severity_score: float,
        remediation_mode: str,
    ) -> ReportResponse:
        return ReportResponse(
            investigation_id=state.investigation_id,
            timeline=[f"Iteration {state.iteration_count} complete"],
            suspects=state.hypotheses[:3],
            citations=["evidence://query-history/placeholder"],
            unresolved_gaps=[] if state.root_cause else ["root cause not finalized"],
            severity_score=severity_score,
            remediation_mode=remediation_mode,
        )
