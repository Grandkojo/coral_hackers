from app.services.template_planner_service import context_anchored_plan
from app.services.trigger_discovery import (
    apply_discovered_context,
    should_skip_schema_catalog,
)


def test_apply_discovered_context_picks_newest_sentry_issue() -> None:
    ctx = {"vercel_deployment_id": "dpl_w3"}
    rows = [
        {
            "sentry_issue_id": "111",
            "error_message": "TypeError: old checkout",
            "first_seen": "2026-05-29T11:09:52Z",
        },
        {
            "sentry_issue_id": "222",
            "error_message": "ValueError: invalid credentials schema",
            "first_seen": "2026-05-29T14:00:00Z",
        },
    ]
    out = apply_discovered_context(ctx, rows)
    assert out["sentry_issue_id"] == "222"
    assert "credentials" in out["sentry_title"]


def test_should_skip_catalog_with_deploy_or_repo() -> None:
    assert should_skip_schema_catalog({"vercel_deployment_id": "dpl_x"})
    assert should_skip_schema_catalog(
        {"github_owner": "o", "github_repo": "r"}
    )
    assert not should_skip_schema_catalog({})


def test_post_deploy_discovery_orders_newest_sentry_first() -> None:
    plan = context_anchored_plan(
        0,
        {"vercel_deployment_id": "dpl_w3", "github_owner": "o", "github_repo": "r"},
    )
    assert plan is not None
    assert "ORDER BY s.first_seen DESC" in plan.sql
