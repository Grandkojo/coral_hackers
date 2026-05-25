from app.schemas.investigation import InvestigationState


class JudgeService:
    """Judge LLM: checks if evidence is sufficient."""

    def has_sufficient_evidence(self, state: InvestigationState) -> bool:
        return state.confidence_score >= 0.6 and len(state.evidence_rows) > 0
