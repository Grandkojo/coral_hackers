import datetime
import json
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    integration = relationship(
        "OrganizationIntegration",
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan",
    )
    investigations = relationship("Investigation", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="users")


class OrganizationIntegration(Base):
    """Per-tenant integration credentials (secrets stored encrypted)."""

    __tablename__ = "organization_integrations"

    id = Column(String, primary_key=True, default=_uuid)
    organization_id = Column(
        String, ForeignKey("organizations.id"), unique=True, nullable=False, index=True
    )
    github_token_enc = Column(Text, default="")
    github_owner = Column(String, default="")
    github_repo = Column(String, default="")
    github_account_type = Column(String, default="org")
    sentry_org = Column(String, default="")
    sentry_token_enc = Column(Text, default="")
    slack_token_enc = Column(Text, default="")
    slack_incident_channel = Column(String, default="incidents")
    vercel_token_enc = Column(Text, default="")
    coral_config_dir = Column(String, default="")
    coral_ready = Column(String, default="false")  # "true" | "false"
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="integration")


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True, index=True)
    status = Column(String, default="running")  # running | complete | failed
    source = Column(String)
    user_query = Column(Text)
    iteration_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)
    root_cause = Column(Text, nullable=True)
    severity_score = Column(Float, nullable=True)
    remediation_mode = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    query_runs = relationship(
        "QueryRun",
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="QueryRun.iteration",
    )
    report = relationship(
        "ReportSnapshot",
        back_populates="investigation",
        uselist=False,
        cascade="all, delete-orphan",
    )
    organization = relationship("Organization", back_populates="investigations")


class QueryRun(Base):
    __tablename__ = "query_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String, ForeignKey("investigations.id"))
    iteration = Column(Integer)
    sql = Column(Text)
    rationale = Column(Text, nullable=True)
    row_count = Column(Integer, default=0)
    _rows_json = Column("rows_json", Text, default="[]")
    ran_at = Column(DateTime, default=datetime.datetime.utcnow)

    investigation = relationship("Investigation", back_populates="query_runs")

    @property
    def rows(self) -> list[dict]:
        return json.loads(self._rows_json)

    @rows.setter
    def rows(self, value: list[dict]) -> None:
        self._rows_json = json.dumps(value)


class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String, ForeignKey("investigations.id"), unique=True)
    _payload_json = Column("payload_json", Text)
    markdown = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    investigation = relationship("Investigation", back_populates="report")

    @property
    def payload(self) -> dict:
        return json.loads(self._payload_json)

    @payload.setter
    def payload(self, value: dict) -> None:
        self._payload_json = json.dumps(value)
