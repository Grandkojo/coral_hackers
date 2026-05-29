from pydantic import BaseModel, Field


class WebhookAcceptedResponse(BaseModel):
    """Immediate ack for provider webhooks (investigation runs in background)."""

    accepted: bool = True
    message: str = "Investigation queued"
    sentry_issue_id: str | None = None
    sentry_short_id: str | None = None
    organization_id: str | None = None
