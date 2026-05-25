from fastapi import APIRouter

from app.schemas.report import ReportResponse
from app.schemas.trigger import TriggerRequest
from app.services.investigation_orchestrator import InvestigationOrchestrator

router = APIRouter(prefix="/triggers", tags=["triggers"])
orchestrator = InvestigationOrchestrator()


@router.post("/dashboard", response_model=ReportResponse)
def trigger_from_dashboard(payload: TriggerRequest) -> ReportResponse:
    payload.source = "dashboard"
    return orchestrator.run(payload)


@router.post("/slack", response_model=ReportResponse)
def trigger_from_slack(payload: TriggerRequest) -> ReportResponse:
    payload.source = "slack"
    return orchestrator.run(payload)


@router.post("/webhook", response_model=ReportResponse)
def trigger_from_webhook(payload: TriggerRequest) -> ReportResponse:
    payload.source = "webhook"
    return orchestrator.run(payload)
