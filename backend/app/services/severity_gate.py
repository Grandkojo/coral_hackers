from app.core.config import settings
from app.schemas.investigation import InvestigationState


class SeverityGate:
    """Controls autonomous vs human-paired remediation.

    Severity is a weighted float in [0, 1]:
      base        — confidence score (certainty of root cause)
      blast_radius — proportional to affected_users count in evidence
      fatal_penalty — +0.15 if any 'fatal' level error is present
      ownership_gap — +0.05 when no owner is confirmed
    """

    @property
    def threshold(self) -> float:
        return settings.severity_threshold

    def calculate_severity(self, state: InvestigationState) -> float:
        base = state.confidence_score

        affected_users = sum(
            int(row.get("affected_users", 0))
            for row in state.evidence_rows
            if isinstance(row.get("affected_users"), (int, float))
        )
        blast_radius = min(0.20, affected_users / 1000)

        has_fatal = any(
            str(row.get("error_level", "")).lower() == "fatal"
            for row in state.evidence_rows
        )
        fatal_penalty = 0.15 if has_fatal else 0.0

        ownership_gap = not any(
            h.text.lower().startswith("owner:") for h in state.hypotheses
        )
        ownership_penalty = 0.05 if ownership_gap else 0.0

        score = base + blast_radius + fatal_penalty + ownership_penalty
        return round(max(0.0, min(1.0, score)), 3)

    def remediation_mode(self, severity: float) -> str:
        if severity <= self.threshold:
            return "autonomous_fix"
        return "human_agent_paired"
