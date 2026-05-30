from app.clients.coral_runtime_client import CoralQueryError, CoralRuntimeClient
from app.core.logging import get_logger

logger = get_logger(__name__)

_READ_ONLY_PREFIXES = ("select", "with", "explain")


class QueryExecutionError(Exception):
    pass


class QueryExecutor:
    """Validates, executes, and normalizes Coral SQL queries."""

    def __init__(self, coral_config_dir: str | None = None) -> None:
        self._coral_config_dir = coral_config_dir
        self._client = CoralRuntimeClient(coral_config_dir=coral_config_dir)

    def set_coral_config_dir(self, coral_config_dir: str | None) -> None:
        if coral_config_dir == self._coral_config_dir:
            return
        self._coral_config_dir = coral_config_dir
        self._client = CoralRuntimeClient(coral_config_dir=coral_config_dir)

    def execute(self, sql: str) -> list[dict]:
        self._guard_read_only(sql)
        try:
            rows = self._client.query(sql)
        except CoralQueryError as exc:
            logger.warning("coral query failed: %s", exc)
            raise QueryExecutionError(str(exc)) from exc
        logger.debug("query returned %d rows", len(rows))
        return self._normalize(rows)

    # ------------------------------------------------------------------

    def _guard_read_only(self, sql: str) -> None:
        stripped = sql.strip().lower()
        if not any(stripped.startswith(p) for p in _READ_ONLY_PREFIXES):
            raise QueryExecutionError(
                f"Only read-only SQL is permitted. Received: {sql[:80]!r}"
            )

    def _normalize(self, rows: list[dict]) -> list[dict]:
        """Ensure every row is a plain dict; drop None-only entries."""
        result = []
        for row in rows:
            if isinstance(row, dict) and any(v is not None for v in row.values()):
                result.append(row)
        return result
