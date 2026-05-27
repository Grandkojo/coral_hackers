import datetime
import json

from sqlalchemy.orm import Session

from app.db.models import Investigation, QueryRun, ReportSnapshot
from app.schemas.investigation import InvestigationState, InvestigationSummary
from app.schemas.query_run import QueryRunResponse
from app.schemas.report import ReportResponse


class EvidenceStore:
    """Persists investigation state, query runs, and reports to the database."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, state: InvestigationState, source: str, user_query: str) -> None:
        investigation = Investigation(
            id=state.investigation_id,
            status=state.status.value,
            source=source,
            user_query=user_query,
        )
        self._db.add(investigation)
        self._db.commit()

    def append_query_run(
        self,
        state: InvestigationState,
        sql: str,
        rationale: str,
        rows: list[dict],
    ) -> str:
        """Persist one query run and return its citation URI."""
        run = QueryRun(
            investigation_id=state.investigation_id,
            iteration=state.iteration_count,
            sql=sql,
            rationale=rationale,
            row_count=len(rows),
            _rows_json=json.dumps(rows),
        )
        self._db.add(run)
        self._db.flush()
        self._db.commit()
        return f"coral://query-run/{run.id}"

    def save(self, state: InvestigationState) -> None:
        """Update iteration + confidence mid-loop."""
        inv = self._db.get(Investigation, state.investigation_id)
        if not inv:
            return
        inv.iteration_count = state.iteration_count
        inv.confidence_score = state.confidence_score
        inv.root_cause = state.root_cause
        inv.status = state.status.value
        self._db.commit()

    def finalize(
        self,
        state: InvestigationState,
        report: ReportResponse,
        severity_score: float,
        remediation_mode: str,
        markdown: str,
    ) -> None:
        inv = self._db.get(Investigation, state.investigation_id)
        if not inv:
            return
        inv.status = "complete"
        inv.severity_score = severity_score
        inv.remediation_mode = remediation_mode
        inv.completed_at = datetime.datetime.now(datetime.timezone.utc)
        snapshot = ReportSnapshot(
            investigation_id=state.investigation_id,
            _payload_json=json.dumps(report.model_dump()),
            markdown=markdown,
        )
        self._db.add(snapshot)
        self._db.commit()

    def get_investigation(self, investigation_id: str) -> Investigation | None:
        return self._db.get(Investigation, investigation_id)

    def list_investigations(self, limit: int = 50) -> list[InvestigationSummary]:
        rows = (
            self._db.query(Investigation)
            .order_by(Investigation.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_investigation_summary(row) for row in rows]

    def get_report(self, investigation_id: str) -> ReportSnapshot | None:
        return (
            self._db.query(ReportSnapshot)
            .filter(ReportSnapshot.investigation_id == investigation_id)
            .first()
        )

    def get_query_runs(self, investigation_id: str) -> list[QueryRunResponse]:
        runs = (
            self._db.query(QueryRun)
            .filter(QueryRun.investigation_id == investigation_id)
            .order_by(QueryRun.iteration)
            .all()
        )
        return [self._to_query_run_response(run) for run in runs]

    def approve_remediation(self, investigation_id: str) -> Investigation:
        inv = self._db.get(Investigation, investigation_id)
        if inv is None:
            raise ValueError("Investigation not found.")
        if inv.remediation_mode != "human_agent_paired":
            raise ValueError(
                f"Investigation remediation_mode is '{inv.remediation_mode}'. "
                "Approval only required for 'human_agent_paired'."
            )
        if inv.approved_at is not None:
            return inv

        inv.approved_at = datetime.datetime.now(datetime.timezone.utc)
        self._db.commit()
        self._db.refresh(inv)
        return inv

    @staticmethod
    def _to_query_run_response(run: QueryRun) -> QueryRunResponse:
        return QueryRunResponse(
            id=run.id,
            investigation_id=run.investigation_id,
            iteration=run.iteration,
            sql=run.sql,
            rationale=run.rationale,
            row_count=run.row_count,
            rows=run.rows,
            citation=f"coral://query-run/{run.id}",
            ran_at=run.ran_at.isoformat() if run.ran_at else None,
        )

    @staticmethod
    def _to_investigation_summary(inv: Investigation) -> InvestigationSummary:
        return InvestigationSummary(
            investigation_id=inv.id,
            status=inv.status,
            source=inv.source,
            user_query=inv.user_query or "",
            iteration_count=inv.iteration_count,
            confidence_score=inv.confidence_score,
            root_cause=inv.root_cause,
            severity_score=inv.severity_score,
            remediation_mode=inv.remediation_mode,
            approved_at=inv.approved_at.isoformat() if inv.approved_at else None,
            created_at=inv.created_at.isoformat() if inv.created_at else None,
            completed_at=inv.completed_at.isoformat() if inv.completed_at else None,
        )
