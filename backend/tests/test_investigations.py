"""Tests for investigation query-runs and approval endpoints."""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Investigation, QueryRun
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    investigation_id = "test-inv-001"
    db = TestingSessionLocal()
    db.add(
        Investigation(
            id=investigation_id,
            status="complete",
            source="dashboard",
            user_query="Why did checkout fail?",
            iteration_count=2,
            confidence_score=0.85,
            root_cause="PR #234 correlated with fatal checkout error",
            severity_score=0.8,
            remediation_mode="human_agent_paired",
        )
    )
    db.add(
        Investigation(
            id="test-inv-002",
            status="complete",
            source="webhook",
            user_query="Sentry spike on python-fastapi",
            iteration_count=3,
            confidence_score=0.62,
            root_cause="Deploy dpl_abc correlated with regression",
            severity_score=0.55,
            remediation_mode="autonomous_fix",
        )
    )
    db.add(
        QueryRun(
            investigation_id=investigation_id,
            iteration=0,
            sql="SELECT * FROM coral.tables LIMIT 10",
            rationale="Discover available Coral sources.",
            row_count=1,
            _rows_json=json.dumps([{"schema_name": "github", "table_name": "pulls"}]),
        )
    )
    db.add(
        QueryRun(
            investigation_id=investigation_id,
            iteration=1,
            sql="SELECT g.number FROM github.pulls g LIMIT 5",
            rationale="Correlate PRs with Sentry errors.",
            row_count=1,
            _rows_json=json.dumps([{"number": 234}]),
        )
    )
    db.commit()
    db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_query_runs_returns_sql_and_rows(client: TestClient) -> None:
    response = client.get("/api/v1/investigations/test-inv-001/query-runs")

    assert response.status_code == 200
    body = response.json()
    assert body["investigation_id"] == "test-inv-001"
    assert len(body["query_runs"]) == 2
    assert body["query_runs"][0]["sql"].startswith("SELECT * FROM coral.tables")
    assert body["query_runs"][0]["citation"] == "coral://query-run/1"
    assert body["query_runs"][1]["rows"][0]["number"] == 234


def test_get_query_runs_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/investigations/missing-id/query-runs")
    assert response.status_code == 404


def test_list_investigations_returns_recent_first(client: TestClient) -> None:
    response = client.get("/api/v1/investigations")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["investigations"]) == 2
    assert body["investigations"][0]["investigation_id"] in {"test-inv-001", "test-inv-002"}
    first = body["investigations"][0]
    assert first["user_query"]
    assert first["severity_score"] is not None


def test_list_investigations_respects_limit(client: TestClient) -> None:
    response = client.get("/api/v1/investigations?limit=1")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["investigations"]) == 1


def test_approve_remediation_persists(client: TestClient) -> None:
    response = client.post("/api/v1/investigations/test-inv-001/approve")

    assert response.status_code == 200
    body = response.json()
    assert body["approved"] is True
    assert body["approved_at"] is not None

    status = client.get("/api/v1/investigations/test-inv-001")
    assert status.json()["approved_at"] is not None


def test_delete_investigation_removes_record(client: TestClient) -> None:
    response = client.delete("/api/v1/investigations/test-inv-002")

    assert response.status_code == 204
    assert client.get("/api/v1/investigations/test-inv-002").status_code == 404

    listed = client.get("/api/v1/investigations").json()
    ids = {item["investigation_id"] for item in listed["investigations"]}
    assert "test-inv-002" not in ids


def test_delete_investigation_not_found(client: TestClient) -> None:
    response = client.delete("/api/v1/investigations/missing-id")
    assert response.status_code == 404


def test_approve_remediation_is_idempotent(client: TestClient) -> None:
    first = client.post("/api/v1/investigations/test-inv-001/approve")
    second = client.post("/api/v1/investigations/test-inv-001/approve")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["approved_at"] == second.json()["approved_at"]
