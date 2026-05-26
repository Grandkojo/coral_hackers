import datetime
import json

from sqlalchemy.orm import Session

from app.db.models import Investigation, QueryRun, ReportSnapshot
from app.schemas.investigation import InvestigationState
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

    def get_report(self, investigation_id: str) -> ReportSnapshot | None:
        return (
            self._db.query(ReportSnapshot)
            .filter(ReportSnapshot.investigation_id == investigation_id)
            .first()
        )
