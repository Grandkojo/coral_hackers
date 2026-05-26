import pytest

from app.schemas.investigation import Hypothesis, InvestigationState
from app.services.severity_gate import SeverityGate


@pytest.fixture()
def gate() -> SeverityGate:
    return SeverityGate()


def _state(
    confidence: float = 0.5,
    evidence: list[dict] | None = None,
    hypotheses: list[Hypothesis] | None = None,
) -> InvestigationState:
    return InvestigationState(
        investigation_id="test-001",
        confidence_score=confidence,
        evidence_rows=evidence or [],
        hypotheses=hypotheses or [],
    )


def test_autonomous_below_threshold(gate: SeverityGate) -> None:
    state = _state(confidence=0.5)
    score = gate.calculate_severity(state)
    assert gate.remediation_mode(score) == "autonomous_fix"


def test_human_paired_above_threshold(gate: SeverityGate) -> None:
    state = _state(
        confidence=0.75,
        evidence=[{"error_level": "fatal", "affected_users": 100}],
    )
    score = gate.calculate_severity(state)
    assert score > 0.7
    assert gate.remediation_mode(score) == "human_agent_paired"


def test_fatal_penalty_increases_score(gate: SeverityGate) -> None:
    without_fatal = gate.calculate_severity(_state(confidence=0.5))
    with_fatal = gate.calculate_severity(
        _state(confidence=0.5, evidence=[{"error_level": "fatal"}])
    )
    assert with_fatal > without_fatal


def test_blast_radius_capped_at_0_20(gate: SeverityGate) -> None:
    state = _state(confidence=0.0, evidence=[{"affected_users": 100_000}])
    score = gate.calculate_severity(state)
    assert score <= 0.20 + 0.05 + 0.001  # blast + ownership_gap + float tolerance


def test_ownership_confirmed_reduces_penalty(gate: SeverityGate) -> None:
    no_owner = gate.calculate_severity(_state(confidence=0.5))
    with_owner = gate.calculate_severity(
        _state(
            confidence=0.5,
            hypotheses=[Hypothesis(text="owner: team=payments oncall=alice", confidence=0.5)],
        )
    )
    assert no_owner > with_owner


def test_score_clamped_to_1(gate: SeverityGate) -> None:
    state = _state(
        confidence=1.0,
        evidence=[{"error_level": "fatal", "affected_users": 5000}],
    )
    score = gate.calculate_severity(state)
    assert score <= 1.0


def test_threshold_boundary_exactly_0_7(gate: SeverityGate) -> None:
    assert gate.remediation_mode(0.70) == "autonomous_fix"
    assert gate.remediation_mode(0.71) == "human_agent_paired"
