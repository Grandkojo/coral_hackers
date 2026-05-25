from pydantic import BaseModel, Field


class ReportResponse(BaseModel):
    investigation_id: str
    timeline: list[str] = Field(default_factory=list)
    suspects: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    unresolved_gaps: list[str] = Field(default_factory=list)
    severity_score: float = 0.0
    remediation_mode: str = Field(
        description="autonomous_fix or human_agent_paired."
    )
