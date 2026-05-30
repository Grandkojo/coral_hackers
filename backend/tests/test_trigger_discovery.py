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


def test_webhook_sentry_only_gets_vercel_correlate_template() -> None:
    plan = context_anchored_plan(
        1,
        {
            "sentry_issue_id": "123540686",
            "sentry_project": "reef-incident-lab-api",
            "github_owner": "reef-demo-org",
            "github_repo": "reef-incident-lab",
        },
    )
    assert plan is not None
    assert "vercel.deployments" in plan.sql
    assert "json_get_str(p.link, 'org')" in plan.sql
    assert "reef-demo-org" in plan.sql
    assert "production" in plan.sql
    assert "INTERVAL" not in plan.sql


def test_webhook_sentry_only_gets_pr_template_without_deploy() -> None:
    plan = context_anchored_plan(
        2,
        {
            "sentry_issue_id": "123540686",
            "github_owner": "reef-demo-org",
            "github_repo": "reef-incident-lab",
        },
    )
    assert plan is not None
    assert "github.pulls" in plan.sql
    assert "WHERE g.owner = 'reef-demo-org'" in plan.sql
    assert "AND g.repo = 'reef-incident-lab'" in plan.sql


def test_post_deploy_discovery_orders_newest_sentry_first() -> None:
    plan = context_anchored_plan(
        0,
        {"vercel_deployment_id": "dpl_w3", "github_owner": "o", "github_repo": "r"},
    )
    assert plan is not None
    assert "ORDER BY s.first_seen DESC" in plan.sql
