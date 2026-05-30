from unittest.mock import patch

from app.core.config import CoralMode, GitHubAccountType, settings
from app.schemas.org_context import OrgContext
from app.services.coral_org_setup import ensure_coral_ready_for_org


def _org(coral_config_dir: str) -> OrgContext:
    return OrgContext(
        organization_id="c4311095-455c-4fbf-9bf1-7005e56e4f03",
        organization_name="Essy Technologies",
        organization_slug="essy-technologies",
        coral_config_dir=coral_config_dir,
        github_token="ghp_test",
        github_account_type=GitHubAccountType.org,
    )


def test_ensure_coral_uses_global_when_org_dir_empty() -> None:
    org_dir = "/data/coral/orgs/c4311095-455c-4fbf-9bf1-7005e56e4f03"
    global_dir = "/data/coral"

    with (
        patch.object(settings, "coral_mode", CoralMode.cli),
        patch(
            "app.services.coral_org_setup.global_coral_config_dir",
            return_value=global_dir,
        ),
        patch("app.services.coral_org_setup.configure_coral_for_org", return_value=True),
        patch(
            "app.services.coral_org_setup.coral_has_any_source",
            side_effect=lambda path: path == global_dir,
        ),
    ):
        effective = ensure_coral_ready_for_org(_org(org_dir))

    assert effective.coral_config_dir == global_dir


def test_ensure_coral_keeps_org_dir_when_sources_present() -> None:
    org_dir = "/data/coral/orgs/c4311095-455c-4fbf-9bf1-7005e56e4f03"

    with (
        patch.object(settings, "coral_mode", CoralMode.cli),
        patch("app.services.coral_org_setup.configure_coral_for_org", return_value=True),
        patch("app.services.coral_org_setup.coral_has_any_source", return_value=True),
    ):
        effective = ensure_coral_ready_for_org(_org(org_dir))

    assert effective.coral_config_dir == org_dir
