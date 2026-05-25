from pydantic import BaseModel, Field


class InvestigationState(BaseModel):
    investigation_id: str
    iteration_count: int = 0
    evidence_rows: list[dict] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    root_cause: str | None = None
