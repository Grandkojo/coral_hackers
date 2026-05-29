from app.core.config import GitHubAccountType
from app.schemas.org_context import OrgContext


def test_persisted_organization_id_legacy_is_none() -> None:
    ctx = OrgContext(
        organization_id="legacy",
        organization_name="Platform default",
        organization_slug="legacy",
        coral_config_dir="/data/coral",
    )
    assert ctx.persisted_organization_id() is None


def test_persisted_organization_id_real_org() -> None:
    ctx = OrgContext(
        organization_id="uuid-123",
        organization_name="Essy",
        organization_slug="essy",
        coral_config_dir="/data/coral",
        github_account_type=GitHubAccountType.org,
    )
    assert ctx.persisted_organization_id() == "uuid-123"
