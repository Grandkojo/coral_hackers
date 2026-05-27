from pydantic import BaseModel, Field


class QueryRunResponse(BaseModel):
    id: int
    investigation_id: str
    iteration: int
    sql: str
    rationale: str | None = None
    row_count: int = 0
    rows: list[dict] = Field(default_factory=list)
    citation: str
    ran_at: str | None = None


class QueryRunListResponse(BaseModel):
    investigation_id: str
    query_runs: list[QueryRunResponse] = Field(default_factory=list)
