import pytest

from app.services.trigger_normalizer import (
    DashboardTriggerRequest,
    extract_vercel_deployment_id,
    normalize_dashboard,
    normalize_sentry_webhook,
    parse_sentry_webhook,
)


def test_extract_vercel_deployment_id_from_url() -> None:
    url = "https://vercel.com/grandkojo/reef/dpl_EEWWZ361mMHt6cnfxB3cFWQkChnv"
    assert extract_vercel_deployment_id(url) == "dpl_EEWWZ361mMHt6cnfxB3cFWQkChnv"


def test_extract_vercel_deployment_id_from_raw_id() -> None:
    assert extract_vercel_deployment_id("dpl_abc123XYZ") == "dpl_abc123XYZ"


def test_normalize_dashboard_nl_only() -> None:
    trigger = normalize_dashboard(
        DashboardTriggerRequest(query="Why did checkout fail after deploy?")
    )
    assert trigger.source == "dashboard"
    assert "checkout" in trigger.query.lower()


def test_normalize_dashboard_vercel_url_generates_query() -> None:
    trigger = normalize_dashboard(
        DashboardTriggerRequest(vercel_url="dpl_test123")
    )
    assert trigger.context["vercel_deployment_id"] == "dpl_test123"
    assert trigger.context["trigger_type"] == "vercel_deployment"
    assert "dpl_test123" in trigger.query


def test_parse_sentry_webhook_issue_created_format() -> None:
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
    context = parse_sentry_webhook(payload)
    assert context["sentry_issue_id"] == "123118378"
    assert context["sentry_short_id"] == "PYTHON-FASTAPI-1"
    assert context["sentry_project"] == "python-fastapi"


def test_normalize_sentry_webhook_builds_trigger() -> None:
    trigger = normalize_sentry_webhook(
        {
            "issue_id": "999",
            "short_id": "DEMO-1",
            "title": "Server exploded",
            "level": "fatal",
            "project": "checkout-service",
        }
    )
    assert trigger.source == "webhook"
    assert trigger.incident_id == "DEMO-1"
    assert trigger.context["sentry_issue_id"] == "999"
    assert "checkout-service" in trigger.query
