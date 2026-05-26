from enum import Enum

from pydantic import BaseModel, Field


class InvestigationStatus(str, Enum):
    running = "running"
    complete = "complete"
    failed = "failed"


class QueryPlan(BaseModel):
    sql: str
    rationale: str
    iteration: int


class Hypothesis(BaseModel):
    text: str
    confidence: float
    source_refs: list[str] = Field(default_factory=list)


class InvestigationState(BaseModel):
    investigation_id: str
    status: InvestigationStatus = InvestigationStatus.running
    iteration_count: int = 0
    query_plans: list[QueryPlan] = Field(default_factory=list)
    evidence_rows: list[dict] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    confidence_score: float = 0.0
    root_cause: str | None = None
    escalation_flags: dict[str, bool] = Field(default_factory=dict)
