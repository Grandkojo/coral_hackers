"""Tests for provider webhook endpoints."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.report import ReportResponse

SAMPLE_REPORT = ReportResponse(
    investigation_id="webhook-test-id",
    timeline=["Iteration 1"],
    suspects=[],
    citations=["coral://query-run/1"],
    unresolved_gaps=[],
    severity_score=0.5,
    remediation_mode="autonomous_fix",
    root_cause="Example root cause",
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_sentry_webhook_starts_investigation(client: TestClient) -> None:
    payload = {
        "action": "created",
        "data": {
            "issue": {
                "id": "123118378",
                "shortId": "PYTHON-FASTAPI-1",
                "title": "Example FastAPI exception",
                "level": "error",
                "project": {"slug": "python-fastapi"},
            }
        },
    }
    with patch(
        "app.api.routes.webhooks.InvestigationOrchestrator.run",
        return_value=SAMPLE_REPORT,
    ) as run_mock:
        response = client.post("/api/v1/webhooks/sentry", json=payload)

    assert response.status_code == 200
    assert response.json()["investigation_id"] == "webhook-test-id"
    trigger = run_mock.call_args.args[0]
    assert trigger.context["sentry_issue_id"] == "123118378"
    assert trigger.context["trigger_type"] == "sentry_webhook"


def test_sentry_webhook_rejects_empty_payload(client: TestClient) -> None:
    response = client.post("/api/v1/webhooks/sentry", json={})
    assert response.status_code == 422


def test_dashboard_accepts_vercel_url_only(client: TestClient) -> None:
    with patch(
        "app.api.routes.triggers.InvestigationOrchestrator.run",
        return_value=SAMPLE_REPORT,
    ) as run_mock:
        response = client.post(
            "/api/v1/triggers/dashboard",
            json={"vercel_url": "dpl_EEWWZ361mMHt6cnfxB3cFWQkChnv"},
        )

    assert response.status_code == 200
    trigger = run_mock.call_args.args[0]
    assert trigger.context["vercel_deployment_id"] == "dpl_EEWWZ361mMHt6cnfxB3cFWQkChnv"
