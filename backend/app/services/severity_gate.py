from app.schemas.investigation import InvestigationState


class SeverityGate:
    """Controls autonomous vs human-paired remediation."""

    threshold: float = 0.7

    def calculate_severity(self, state: InvestigationState) -> float:
        # Placeholder strategy. Replace with weighted model:
        # impact + blast radius + confidence in root cause.
        base = state.confidence_score
        penalty = 0.1 if len(state.evidence_rows) < 2 else 0.0
        return max(0.0, min(1.0, base + penalty))

    def remediation_mode(self, severity: float) -> str:
        if severity <= self.threshold:
            return "autonomous_fix"
        return "human_agent_paired"
