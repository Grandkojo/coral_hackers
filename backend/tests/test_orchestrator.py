"""Integration test for the full investigation loop using mock Coral data."""
import pytest
from unittest.mock import MagicMock

from app.schemas.trigger import TriggerRequest
from app.services.evidence_store import EvidenceStore
from app.services.investigation_orchestrator import InvestigationOrchestrator


def _mock_store() -> EvidenceStore:
    store = MagicMock(spec=EvidenceStore)
    store.append_query_run.return_value = "coral://query-run/1"
    return store


@pytest.fixture()
def orchestrator() -> InvestigationOrchestrator:
    return InvestigationOrchestrator(evidence_store=_mock_store())


def test_run_returns_report(orchestrator: InvestigationOrchestrator) -> None:
    trigger = TriggerRequest(
        source="dashboard",
        query="Why did checkout fail after the last deploy?",
    )
    report = orchestrator.run(trigger)
    assert report.investigation_id
    assert report.severity_score >= 0.0
    assert report.remediation_mode in ("autonomous_fix", "human_agent_paired")


def test_run_finds_root_cause(orchestrator: InvestigationOrchestrator) -> None:
    trigger = TriggerRequest(
        source="dashboard",
        query="Why did checkout fail after the last deploy?",
    )
    report = orchestrator.run(trigger)
    assert report.root_cause is not None
    assert "PR" in report.root_cause or "pr" in report.root_cause.lower()


def test_run_has_citations(orchestrator: InvestigationOrchestrator) -> None:
    trigger = TriggerRequest(source="webhook", query="checkout errors spiking")
    report = orchestrator.run(trigger)
    assert len(report.citations) > 0
    assert all(c.startswith("coral://") for c in report.citations)


def test_run_has_timeline(orchestrator: InvestigationOrchestrator) -> None:
    trigger = TriggerRequest(source="slack", query="payment failures after deploy")
    report = orchestrator.run(trigger)
    assert len(report.timeline) > 0


def test_run_suspects_are_strings(orchestrator: InvestigationOrchestrator) -> None:
    trigger = TriggerRequest(source="dashboard", query="checkout down")
    report = orchestrator.run(trigger)
    assert all(isinstance(s, str) for s in report.suspects)


def test_evidence_store_called(orchestrator: InvestigationOrchestrator) -> None:
    trigger = TriggerRequest(source="dashboard", query="checkout failure")
    orchestrator.run(trigger)
    orchestrator.evidence_store.create.assert_called_once()
    orchestrator.evidence_store.finalize.assert_called_once()
