from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import SessionPrincipal, get_current_principal
from app.db.session import get_db
from app.schemas.investigation import InvestigationListResponse
from app.schemas.query_run import QueryRunListResponse
from app.schemas.report import ReportResponse
from app.services.evidence_store import EvidenceStore

router = APIRouter(prefix="/investigations", tags=["investigations"])


def _store(db: Session = Depends(get_db)) -> EvidenceStore:
    return EvidenceStore(db)


@router.get("", response_model=InvestigationListResponse)
def list_investigations(
    limit: int = Query(default=50, ge=1, le=100),
    store: EvidenceStore = Depends(_store),
    principal: SessionPrincipal = Depends(get_current_principal),
) -> InvestigationListResponse:
    """List recent investigations for the signed-in organization."""
    org_id = principal.organization.id
    if org_id == "legacy":
        org_id = None
    investigations = store.list_investigations(limit=limit, organization_id=org_id)
    return InvestigationListResponse(
        investigations=investigations,
        total=len(investigations),
    )


def _assert_org_access(inv, principal: SessionPrincipal) -> None:
    org_id = principal.organization.id
    if org_id == "legacy":
        return
    if inv.organization_id and inv.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Investigation not found.")


@router.get("/{investigation_id}")
def get_investigation(
    investigation_id: str,
    store: EvidenceStore = Depends(_store),
    principal: SessionPrincipal = Depends(get_current_principal),
) -> dict:
    """Poll investigation status and live confidence score."""
    inv = store.get_investigation(investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    _assert_org_access(inv, principal)
    return {
        "investigation_id": inv.id,
        "status": inv.status,
        "source": inv.source,
        "iteration_count": inv.iteration_count,
        "confidence_score": inv.confidence_score,
        "root_cause": inv.root_cause,
        "severity_score": inv.severity_score,
        "remediation_mode": inv.remediation_mode,
        "approved_at": inv.approved_at.isoformat() if inv.approved_at else None,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "completed_at": inv.completed_at.isoformat() if inv.completed_at else None,
    }


@router.get("/{investigation_id}/report", response_model=ReportResponse)
def get_report(
    investigation_id: str,
    store: EvidenceStore = Depends(_store),
    principal: SessionPrincipal = Depends(get_current_principal),
) -> ReportResponse:
    """Retrieve the finalized investigation report."""
    inv = store.get_investigation(investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    _assert_org_access(inv, principal)
    snapshot = store.get_report(investigation_id)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail="Report not available yet — investigation may still be running.",
        )
    return ReportResponse(**snapshot.payload)


@router.get("/{investigation_id}/query-runs", response_model=QueryRunListResponse)
def get_query_runs(
    investigation_id: str,
    store: EvidenceStore = Depends(_store),
    principal: SessionPrincipal = Depends(get_current_principal),
) -> QueryRunListResponse:
    """Return SQL, rationale, and row results for each investigation iteration."""
    inv = store.get_investigation(investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    _assert_org_access(inv, principal)
    return QueryRunListResponse(
        investigation_id=investigation_id,
        query_runs=store.get_query_runs(investigation_id),
    )


@router.delete("/{investigation_id}", status_code=204)
def delete_investigation(
    investigation_id: str,
    store: EvidenceStore = Depends(_store),
    principal: SessionPrincipal = Depends(get_current_principal),
) -> None:
    """Remove an investigation and its query runs / report snapshot."""
    inv = store.get_investigation(investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    _assert_org_access(inv, principal)
    store.delete_investigation(investigation_id)


@router.post("/{investigation_id}/approve")
def approve_remediation(
    investigation_id: str,
    store: EvidenceStore = Depends(_store),
    principal: SessionPrincipal = Depends(get_current_principal),
) -> dict:
    """Human approval gate for high-severity (human_agent_paired) investigations."""
    inv = store.get_investigation(investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    _assert_org_access(inv, principal)
    try:
        inv = store.approve_remediation(investigation_id)
    except ValueError as exc:
        detail = str(exc)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc

    return {
        "investigation_id": investigation_id,
        "approved": True,
        "approved_at": inv.approved_at.isoformat() if inv.approved_at else None,
        "message": "Remediation approved — autonomous fix workflow will proceed.",
    }
