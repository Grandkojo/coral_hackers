"""Tests for provider webhook endpoints."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.org_context import OrgContext
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

MOCK_ORG = OrgContext(
    organization_id="org-1",
    organization_name="Essy",
    organization_slug="essy",
    coral_config_dir="/tmp/coral",
    sentry_org="essytech",
    coral_ready=True,
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_sentry_webhook_accepts_and_queues(client: TestClient) -> None:
    payload = {
        "action": "created",
        "organization": {"slug": "essytech"},
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
    with (
        patch(
            "app.api.routes.webhooks.WebhookOrgResolver.resolve_for_sentry",
            return_value=MOCK_ORG,
        ),
        patch(
            "app.api.routes.webhooks.process_sentry_webhook",
        ) as worker_mock,
    ):
        response = client.post("/api/v1/webhooks/sentry", json=payload)

    assert response.status_code == 202
    body = response.json()
    assert body["accepted"] is True
    assert body["sentry_issue_id"] == "123118378"
    assert body["organization_id"] == "org-1"
    worker_mock.assert_called_once()


def test_sentry_webhook_rejects_empty_payload(client: TestClient) -> None:
    response = client.post("/api/v1/webhooks/sentry", json={})
    assert response.status_code == 400


def test_sentry_webhook_requires_org_context(client: TestClient) -> None:
    payload = {
        "data": {
            "issue": {
                "id": "1",
                "shortId": "X-1",
                "title": "err",
                "project": {"slug": "p"},
            }
        },
    }
    with patch(
        "app.api.routes.webhooks.WebhookOrgResolver.resolve_for_sentry",
        return_value=None,
    ):
        response = client.post("/api/v1/webhooks/sentry", json=payload)
    assert response.status_code == 503


def test_parse_sentry_webhook_includes_org_slug() -> None:
    from app.services.trigger_normalizer import parse_sentry_webhook

    ctx = parse_sentry_webhook(
        {"organization": {"slug": "essytech"}, "data": {"issue": {"id": "9"}}}
    )
    assert ctx["sentry_org_slug"] == "essytech"


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
