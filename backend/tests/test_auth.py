"""Tests for organization signup, login, and profile APIs."""
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import CoralMode, settings
from app.db.models import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "auth_required", True)
    monkeypatch.setattr(settings, "coral_mode", CoralMode.mock)
    monkeypatch.setattr(settings, "coral_orgs_base_dir", tempfile.mkdtemp())

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_signup_login_and_profile(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.org_integration_service.configure_coral_for_org",
        lambda _org: True,
    )

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "organization_name": "Reef Demo Org",
            "email": "admin@reefdemo.com",
            "password": "securepass123",
            "full_name": "Demo Admin",
        },
    )
    assert signup.status_code == 201
    token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["organization"]["slug"] == "reef-demo-org"

    profile = client.get("/api/v1/organizations/me/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["coral_ready"] is False

    update = client.put(
        "/api/v1/organizations/me/credentials",
        headers=headers,
        json={
            "github_token": "ghp_test_token",
            "github_owner": "reef-demo-org",
            "github_repo": "reef-incident-lab",
            "github_account_type": "org",
            "sentry_org": "reef-sentry",
            "sentry_token": "sntrys_test",
            "slack_token": "xoxb-test",
            "vercel_token": "vercel_test",
        },
    )
    assert update.status_code == 200
    assert update.json()["profile"]["has_github"] is True
    assert update.json()["coral_ready"] is True


def test_dashboard_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triggers/dashboard",
        json={"query": "Why did checkout fail?"},
    )
    assert response.status_code == 401
