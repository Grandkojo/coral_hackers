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
    query_row_counts: list[int] = Field(default_factory=list)
    last_query_row_count: int | None = None
    evidence_rows: list[dict] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    confidence_score: float = 0.0
    root_cause: str | None = None
    escalation_flags: dict[str, bool] = Field(default_factory=dict)
    trigger_context: dict[str, str] = Field(default_factory=dict)
    github_queries_executed: int = 0
    github_rate_limited: bool = False


class InvestigationSummary(BaseModel):
    investigation_id: str
    status: str
    source: str
    user_query: str
    iteration_count: int = 0
    confidence_score: float = 0.0
    root_cause: str | None = None
    severity_score: float | None = None
    remediation_mode: str | None = None
    approved_at: str | None = None
    created_at: str | None = None
    completed_at: str | None = None


class InvestigationListResponse(BaseModel):
    investigations: list[InvestigationSummary] = Field(default_factory=list)
    total: int = 0
