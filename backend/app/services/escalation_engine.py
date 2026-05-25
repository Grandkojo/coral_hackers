from app.schemas.investigation import InvestigationState


class EscalationEngine:
    """Evaluates rule-based escalation checks before reporting/remediation."""

    def evaluate(self, state: InvestigationState) -> dict[str, bool]:
        return {
            "sufficient_evidence": state.confidence_score >= 0.6,
            "conflicting_hypotheses": len(state.hypotheses) > 3,
            "missing_ownership": not any("owner:" in h.lower() for h in state.hypotheses),
        }
