from typing import Any

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.schemas.org_context import OrgContext
from app.schemas.trigger import TriggerRequest
from app.services.evidence_store import EvidenceStore
from app.services.investigation_orchestrator import InvestigationOrchestrator
from app.services.trigger_normalizer import normalize_sentry_webhook
from app.services.webhook_notifications import notify_sentry_investigation_complete
from app.services.webhook_org_resolver import WebhookOrgResolver

logger = get_logger(__name__)


async def process_sentry_webhook(
    payload: dict[str, Any],
    *,
    organization_id: str | None = None,
) -> None:
    """Run investigation and post results to Slack (separate DB session)."""
    trigger = normalize_sentry_webhook(payload)
    db = SessionLocal()
    org_context: OrgContext | None = None
    try:
        resolver = WebhookOrgResolver(db)
        if organization_id:
            from app.db.models import Organization

            org = db.get(Organization, organization_id)
            if org is not None:
                from app.services.org_integration_service import OrgIntegrationService

                org_context = OrgIntegrationService(db).build_org_context(org)
        if org_context is None:
            org_context = resolver.resolve_for_sentry(payload)

        if org_context is None:
            logger.error("sentry webhook aborted: no organization context")
            return

        orchestrator = InvestigationOrchestrator(
            evidence_store=EvidenceStore(db),
            org_context=org_context,
        )
        report = orchestrator.run(trigger)
        await notify_sentry_investigation_complete(
            report,
            org_context=org_context,
            sentry_short_id=trigger.context.get("sentry_short_id", ""),
            sentry_title=trigger.context.get("sentry_title", ""),
        )
        logger.info(
            "sentry webhook investigation complete id=%s org=%s",
            report.investigation_id,
            org_context.organization_slug,
        )
    except Exception:
        logger.exception("sentry webhook investigation failed")
    finally:
        db.close()
