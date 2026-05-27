from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import ReportResponse
from app.services.evidence_store import EvidenceStore
from app.services.investigation_orchestrator import InvestigationOrchestrator
from app.services.trigger_normalizer import normalize_sentry_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _orchestrator(db: Session = Depends(get_db)) -> InvestigationOrchestrator:
    return InvestigationOrchestrator(evidence_store=EvidenceStore(db))


@router.post("/sentry", response_model=ReportResponse)
async def sentry_webhook(
    request: Request,
    orchestrator: InvestigationOrchestrator = Depends(_orchestrator),
) -> ReportResponse:
    """Accept Sentry issue/alert webhooks and start an investigation."""
    try:
        payload: dict[str, Any] = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    if payload is None:
        raise HTTPException(status_code=400, detail="Empty webhook payload")

    context = normalize_sentry_webhook(payload).context
    if not context.get("sentry_issue_id") and not context.get("sentry_short_id"):
        raise HTTPException(
            status_code=422,
            detail="Could not extract a Sentry issue from webhook payload",
        )

    trigger = normalize_sentry_webhook(payload)
    return orchestrator.run(trigger)
