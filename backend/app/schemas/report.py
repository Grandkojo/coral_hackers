from pydantic import BaseModel, Field


class ReportResponse(BaseModel):
    investigation_id: str
    timeline: list[str] = Field(default_factory=list)
    suspects: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    unresolved_gaps: list[str] = Field(default_factory=list)
    severity_score: float = 0.0
    remediation_mode: str = Field(description="autonomous_fix or human_agent_paired.")
    root_cause: str | None = None
    github_queries_executed: int = 0
    github_queries_max: int = 2
    github_rate_limited: bool = False
