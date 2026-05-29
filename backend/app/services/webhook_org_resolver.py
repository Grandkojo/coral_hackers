from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import Organization, OrganizationIntegration
from app.schemas.org_context import OrgContext
from app.services.org_integration_service import OrgIntegrationService

logger = get_logger(__name__)


def extract_sentry_org_slug(payload: dict) -> str:
    """Best-effort Sentry organization slug from webhook JSON."""
    for key in ("organization", "installation"):
        block = payload.get(key)
        if isinstance(block, dict):
            slug = block.get("slug") or block.get("id")
            if slug:
                return str(slug).strip()

    org = payload.get("organization")
    if isinstance(org, str) and org.strip():
        return org.strip()

    actor = payload.get("actor")
    if isinstance(actor, dict):
        slug = actor.get("slug")
        if slug:
            return str(slug).strip()

    return ""


class WebhookOrgResolver:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._integrations = OrgIntegrationService(db)

    def resolve_for_sentry(self, payload: dict) -> OrgContext | None:
        """Map webhook to tenant Coral credentials."""
        if settings.webhook_organization_id.strip():
            org = self._db.get(Organization, settings.webhook_organization_id.strip())
            if org is None:
                logger.warning(
                    "WEBHOOK_ORGANIZATION_ID=%s not found",
                    settings.webhook_organization_id,
                )
            else:
                ctx = self._integrations.build_org_context(org)
                if ctx.coral_ready or settings.coral_mode.value == "mock":
                    return ctx
                logger.warning("webhook org %s coral not ready", org.slug)

        slug = extract_sentry_org_slug(payload)
        if slug:
            row = (
                self._db.query(OrganizationIntegration)
                .filter(OrganizationIntegration.sentry_org.ilike(slug))
                .first()
            )
            if row is not None:
                org = self._db.get(Organization, row.organization_id)
                if org is not None:
                    ctx = self._integrations.build_org_context(org)
                    if ctx.coral_ready or settings.coral_mode.value == "mock":
                        return ctx
                    logger.warning(
                        "sentry org slug %s matched reef org %s but coral not ready",
                        slug,
                        org.slug,
                    )

        legacy = OrgIntegrationService.legacy_context_from_settings()
        if legacy is not None:
            logger.info("webhook using legacy platform credentials")
            return legacy

        logger.error(
            "no reef org for sentry webhook (slug=%r, set WEBHOOK_ORGANIZATION_ID)",
            slug or None,
        )
        return None
