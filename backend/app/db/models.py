import datetime
import json

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(String, primary_key=True)
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
