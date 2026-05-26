from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import ReportResponse
from app.services.evidence_store import EvidenceStore

router = APIRouter(prefix="/investigations", tags=["investigations"])


def _store(db: Session = Depends(get_db)) -> EvidenceStore:
    return EvidenceStore(db)


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


@router.post("/{investigation_id}/approve")
def approve_remediation(
    investigation_id: str, store: EvidenceStore = Depends(_store)
) -> dict:
    """Human approval gate for high-severity (human_agent_paired) investigations."""
    inv = store.get_investigation(investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    if inv.remediation_mode != "human_agent_paired":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Investigation remediation_mode is '{inv.remediation_mode}'. "
                "Approval only required for 'human_agent_paired'."
            ),
        )
    return {
        "investigation_id": investigation_id,
        "approved": True,
        "message": "Remediation approved — autonomous fix workflow will proceed.",
    }
