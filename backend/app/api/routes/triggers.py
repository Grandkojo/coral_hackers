from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import ReportResponse
from app.schemas.trigger import TriggerRequest
from app.services.evidence_store import EvidenceStore
from app.services.investigation_orchestrator import InvestigationOrchestrator
from app.services.trigger_normalizer import (
    DashboardTriggerRequest,
    normalize_dashboard,
    normalize_sentry_webhook,
)

router = APIRouter(prefix="/triggers", tags=["triggers"])


def _orchestrator(db: Session = Depends(get_db)) -> InvestigationOrchestrator:
    return InvestigationOrchestrator(evidence_store=EvidenceStore(db))


def _run(orchestrator: InvestigationOrchestrator, trigger: TriggerRequest) -> ReportResponse:
    return orchestrator.run(trigger)


@router.post("/dashboard", response_model=ReportResponse)
def trigger_from_dashboard(
    payload: DashboardTriggerRequest,
    orchestrator: InvestigationOrchestrator = Depends(_orchestrator),
) -> ReportResponse:
    trigger = normalize_dashboard(payload)
    return _run(orchestrator, trigger)


@router.post("/slack", response_model=ReportResponse)
def trigger_from_slack(
    payload: TriggerRequest,
    orchestrator: InvestigationOrchestrator = Depends(_orchestrator),
) -> ReportResponse:
    payload.source = "slack"
    return _run(orchestrator, payload)


@router.post("/webhook", response_model=ReportResponse)
def trigger_from_webhook(
    payload: TriggerRequest,
    orchestrator: InvestigationOrchestrator = Depends(_orchestrator),
) -> ReportResponse:
    payload.source = "webhook"
    return _run(orchestrator, payload)
