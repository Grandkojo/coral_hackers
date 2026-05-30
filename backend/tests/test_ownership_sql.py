from app.core.config import GitHubAccountType
from app.services.template_planner_service import _ownership_sql


def test_org_with_repo_uses_collaborators_not_teams() -> None:
    sql, _ = _ownership_sql(
        "reef-demo-org",
        "reef-incident-lab",
        {"github_account_type": GitHubAccountType.org.value},
    )
    assert "github.collaborators" in sql
    assert "github.teams" not in sql


def test_org_without_repo_uses_teams() -> None:
    sql, _ = _ownership_sql(
        "reef-demo-org",
        "",
        {"github_account_type": GitHubAccountType.org.value},
    )
    assert "github.teams" in sql
