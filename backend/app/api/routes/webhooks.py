from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.webhook import WebhookAcceptedResponse
from app.services.sentry_webhook_worker import process_sentry_webhook
from app.services.trigger_normalizer import normalize_sentry_webhook
from app.services.webhook_org_resolver import WebhookOrgResolver

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/sentry", response_model=WebhookAcceptedResponse, status_code=202)
async def sentry_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> WebhookAcceptedResponse:
    """Accept Sentry webhooks, queue investigation, post report to Slack when done."""
    try:
        payload: dict[str, Any] = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    if not payload:
        raise HTTPException(status_code=400, detail="Empty webhook payload")

    context = normalize_sentry_webhook(payload).context
    if not context.get("sentry_issue_id") and not context.get("sentry_short_id"):
        raise HTTPException(
            status_code=422,
            detail="Could not extract a Sentry issue from webhook payload",
        )

    org_context = WebhookOrgResolver(db).resolve_for_sentry(payload)
    if org_context is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "No Reef organization configured for this Sentry webhook. "
                "Set WEBHOOK_ORGANIZATION_ID or match sentry_org on an org profile."
            ),
        )

    org_id = (
        settings.webhook_organization_id.strip() or org_context.organization_id
    )
    background_tasks.add_task(
        process_sentry_webhook,
        payload,
        organization_id=org_id if org_id != "legacy" else None,
    )

    return WebhookAcceptedResponse(
        message="Investigation queued; report will post to Slack when complete.",
        sentry_issue_id=context.get("sentry_issue_id"),
        sentry_short_id=context.get("sentry_short_id"),
        organization_id=org_context.organization_id,
    )
