from pydantic import BaseModel, Field


class TriggerRequest(BaseModel):
    source: str = Field(description="Trigger source: dashboard, slack, or webhook.")
    incident_id: str | None = Field(
        default=None, description="External incident identifier if available."
    )
    query: str = Field(description="Natural-language investigation prompt.")
    context: dict[str, str] = Field(
        default_factory=dict, description="Optional source-specific metadata."
    )


class TriggerResponse(BaseModel):
    investigation_id: str
    status: str = "running"
    message: str = "Investigation started."
    poll_url: str
