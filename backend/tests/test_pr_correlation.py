from app.services.template_planner_service import context_anchored_plan


def test_pr_query_only_includes_post_deploy_merges() -> None:
    plan = context_anchored_plan(
        2,
        {
            "vercel_deployment_id": "dpl_w3",
            "sentry_issue_id": "123581968",
            "github_owner": "reef-demo-org",
            "github_repo": "reef-incident-lab",
        },
    )
    assert plan is not None
    assert "merged_at >= d.created_at" in plan.sql
    assert "created_at - INTERVAL '4' HOUR" not in plan.sql
