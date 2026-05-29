from app.schemas.investigation import InvestigationState


class EscalationEngine:
    """Evaluates rule-based escalation checks before reporting / remediation."""

    def evaluate(self, state: InvestigationState) -> dict[str, bool]:
        has_owner = any(
            h.text.lower().startswith("owner:")
            or h.text.lower().startswith("change_author:")
            for h in state.hypotheses
        )
        high_confidence_hypotheses = [
            h for h in state.hypotheses if h.confidence >= 0.5
        ]
        conflicting = (
            len(state.hypotheses) > 3
            and max((h.confidence for h in state.hypotheses), default=0.0) < 0.5
        )
        return {
            "sufficient_evidence": state.confidence_score >= 0.6,
            "conflicting_hypotheses": conflicting,
            "missing_ownership": not has_owner,
            "strong_hypothesis_count": len(high_confidence_hypotheses),  # type: ignore[dict-item]
        }
