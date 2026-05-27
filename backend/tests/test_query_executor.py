import pytest

from app.services.query_executor import QueryExecutionError, QueryExecutor


@pytest.fixture()
def executor() -> QueryExecutor:
    return QueryExecutor()


def test_mock_catalog_probe_returns_rows(executor: QueryExecutor) -> None:
    rows = executor.execute("SELECT * FROM coral.tables LIMIT 50")
    assert len(rows) > 0
    assert all(isinstance(r, dict) for r in rows)


def test_mock_deploy_error_join_returns_rows(executor: QueryExecutor) -> None:
    sql = """SELECT g.title, s.message FROM github.pull_requests g
             JOIN sentry.issues s ON s.first_seen >= g.merged_at
             WHERE s.level = 'fatal'"""
    rows = executor.execute(sql)
    assert len(rows) > 0
    assert any(r.get("error_level") == "fatal" for r in rows)


def test_mock_slack_messages_returns_rows(executor: QueryExecutor) -> None:
    rows = executor.execute(
        "SELECT text, user FROM slack.messages WHERE channel = '#incidents'"
    )
    assert len(rows) > 0
    assert all("text" in r for r in rows)


def test_read_only_guard_rejects_insert(executor: QueryExecutor) -> None:
    with pytest.raises(QueryExecutionError, match="read-only"):
        executor.execute("INSERT INTO sentry.issues VALUES (1, 'x')")


def test_read_only_guard_rejects_drop(executor: QueryExecutor) -> None:
    with pytest.raises(QueryExecutionError, match="read-only"):
        executor.execute("DROP TABLE github.pull_requests")


def test_normalization_drops_all_none_rows(executor: QueryExecutor) -> None:
    rows = executor.execute("SELECT * FROM coral.tables LIMIT 50")
    assert all(any(v is not None for v in r.values()) for r in rows)
