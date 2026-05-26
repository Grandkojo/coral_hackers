from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import ReportResponse
from app.schemas.trigger import TriggerRequest
from app.services.evidence_store import EvidenceStore
from app.services.investigation_orchestrator import InvestigationOrchestrator

router = APIRouter(prefix="/triggers", tags=["triggers"])


def _orchestrator(db: Session = Depends(get_db)) -> InvestigationOrchestrator:
    return InvestigationOrchestrator(evidence_store=EvidenceStore(db))


@router.post("/dashboard", response_model=ReportResponse)
def trigger_from_dashboard(
    payload: TriggerRequest,
    orchestrator: InvestigationOrchestrator = Depends(_orchestrator),
) -> ReportResponse:
    payload.source = "dashboard"
    return orchestrator.run(payload)


@router.post("/slack", response_model=ReportResponse)
def trigger_from_slack(
    payload: TriggerRequest,
    orchestrator: InvestigationOrchestrator = Depends(_orchestrator),
) -> ReportResponse:
    payload.source = "slack"
    return orchestrator.run(payload)


@router.post("/webhook", response_model=ReportResponse)
def trigger_from_webhook(
    payload: TriggerRequest,
    orchestrator: InvestigationOrchestrator = Depends(_orchestrator),
) -> ReportResponse:
    payload.source = "webhook"
    return orchestrator.run(payload)
