"""API-level tests for trigger endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.core.config import CoralMode, settings
from app.main import app
from app.schemas.report import ReportResponse


SAMPLE_REPORT = ReportResponse(
    investigation_id="test-id-001",
    timeline=["Iteration 1: catalog probe", "Root cause identified: PR #234"],
    suspects=["PR #234 'feat: refactor checkout' by diana.reyes may have introduced: TypeError"],
    citations=["coral://query-run/1", "coral://query-run/2"],
    unresolved_gaps=[],
    severity_score=0.85,
    remediation_mode="human_agent_paired",
    root_cause="PR #234 may have introduced: TypeError: Cannot read properties of undefined",
)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "coral_mode", CoralMode.mock)
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_trigger_returns_report(client: TestClient) -> None:
    with patch(
        "app.api.routes.triggers.InvestigationOrchestrator.run",
        return_value=SAMPLE_REPORT,
    ):
        response = client.post(
            "/api/v1/triggers/dashboard",
            json={"source": "dashboard", "query": "Why did checkout fail?"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["investigation_id"] == "test-id-001"
    assert body["remediation_mode"] == "human_agent_paired"
    assert body["root_cause"] is not None


def test_slack_trigger_returns_report(client: TestClient) -> None:
    with patch(
        "app.api.routes.triggers.InvestigationOrchestrator.run",
        return_value=SAMPLE_REPORT,
    ):
        response = client.post(
            "/api/v1/triggers/slack",
            json={"source": "slack", "query": "checkout errors spiking"},
        )
    assert response.status_code == 200
    assert response.json()["severity_score"] == 0.85


def test_trigger_missing_query_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triggers/dashboard",
        json={"source": "dashboard"},
    )
    assert response.status_code == 422


def test_trigger_real_loop_mock_coral() -> None:
    """End-to-end with real orchestrator loop and SQLite DB (CORAL_MODE=mock)."""
    with TestClient(app) as c:
        response = c.post(
            "/api/v1/triggers/dashboard",
            json={
                "source": "dashboard",
                "query": "Why did checkout fail after the last deploy?",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["investigation_id"]
    assert body["severity_score"] >= 0.0
    assert body["remediation_mode"] in ("autonomous_fix", "human_agent_paired")
    assert len(body["citations"]) > 0
    assert body["root_cause"] is not None
