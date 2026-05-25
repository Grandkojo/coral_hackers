from app.schemas.investigation import InvestigationState


class EvidenceStore:
    """Persists evidence and confidence snapshots."""

    def save(self, state: InvestigationState) -> None:
        # TODO: Replace with SQLAlchemy repository backed by PostgreSQL/SQLite.
        _ = state
