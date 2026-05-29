from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import SessionPrincipal, get_current_principal, require_org_coral_ready
from app.services.org_integration_service import OrgIntegrationService
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


def _orchestrator_for_org(
    db: Session = Depends(get_db),
    principal: SessionPrincipal = Depends(require_org_coral_ready),
) -> InvestigationOrchestrator:
    return InvestigationOrchestrator(
        evidence_store=EvidenceStore(db),
        org_context=principal.org_context,
    )


def _orchestrator_legacy(db: Session = Depends(get_db)) -> InvestigationOrchestrator:
    legacy = OrgIntegrationService.legacy_context_from_settings()
    return InvestigationOrchestrator(
        evidence_store=EvidenceStore(db),
        org_context=legacy,
    )


def _run(orchestrator: InvestigationOrchestrator, trigger: TriggerRequest) -> ReportResponse:
    return orchestrator.run(trigger)


@router.post("/dashboard", response_model=ReportResponse)
def trigger_from_dashboard(
    payload: DashboardTriggerRequest,
    orchestrator: InvestigationOrchestrator = Depends(_orchestrator_for_org),
) -> ReportResponse:
    trigger = normalize_dashboard(payload)
    return _run(orchestrator, trigger)


@router.post("/slack", response_model=ReportResponse)
def trigger_from_slack(
    payload: TriggerRequest,
    orchestrator: InvestigationOrchestrator = Depends(_orchestrator_legacy),
) -> ReportResponse:
    payload.source = "slack"
    return _run(orchestrator, payload)


@router.post("/webhook", response_model=ReportResponse)
def trigger_from_webhook(
    payload: TriggerRequest,
    orchestrator: InvestigationOrchestrator = Depends(_orchestrator_legacy),
) -> ReportResponse:
    payload.source = "webhook"
    return _run(orchestrator, payload)
