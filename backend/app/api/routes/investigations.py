from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

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
) -> InvestigationListResponse:
    """List recent investigations, newest first."""
    investigations = store.list_investigations(limit=limit)
    return InvestigationListResponse(
        investigations=investigations,
        total=len(investigations),
    )


@router.get("/{investigation_id}")
def get_investigation(
    investigation_id: str, store: EvidenceStore = Depends(_store)
) -> dict:
    """Poll investigation status and live confidence score."""
    inv = store.get_investigation(investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")
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
    investigation_id: str, store: EvidenceStore = Depends(_store)
) -> ReportResponse:
    """Retrieve the finalized investigation report."""
    snapshot = store.get_report(investigation_id)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail="Report not available yet — investigation may still be running.",
        )
    return ReportResponse(**snapshot.payload)


@router.get("/{investigation_id}/query-runs", response_model=QueryRunListResponse)
def get_query_runs(
    investigation_id: str, store: EvidenceStore = Depends(_store)
) -> QueryRunListResponse:
    """Return SQL, rationale, and row results for each investigation iteration."""
    inv = store.get_investigation(investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    return QueryRunListResponse(
        investigation_id=investigation_id,
        query_runs=store.get_query_runs(investigation_id),
    )


@router.post("/{investigation_id}/approve")
def approve_remediation(
    investigation_id: str, store: EvidenceStore = Depends(_store)
) -> dict:
    """Human approval gate for high-severity (human_agent_paired) investigations."""
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
