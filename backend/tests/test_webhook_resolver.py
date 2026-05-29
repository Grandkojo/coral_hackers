from unittest.mock import MagicMock, patch

from app.db.models import Organization
from app.services.webhook_org_resolver import WebhookOrgResolver, extract_sentry_org_slug


def test_extract_sentry_org_slug() -> None:
    assert extract_sentry_org_slug({"organization": {"slug": "essytech"}}) == "essytech"


def test_resolve_prefers_webhook_organization_id() -> None:
    db = MagicMock()
    org = MagicMock()
    org.slug = "essy"
    db.get.return_value = org
    ctx = MagicMock()
    ctx.coral_ready = True

    with (
        patch("app.services.webhook_org_resolver.settings") as settings,
        patch(
            "app.services.webhook_org_resolver.OrgIntegrationService"
        ) as svc_cls,
    ):
        settings.webhook_organization_id = "fixed-org-id"
        settings.coral_mode.value = "cli"
        svc_cls.return_value.build_org_context.return_value = ctx
        result = WebhookOrgResolver(db).resolve_for_sentry({})

    assert result is ctx
    db.get.assert_called_with(Organization, "fixed-org-id")
