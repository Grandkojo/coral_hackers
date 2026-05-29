import re
from typing import Any

from pydantic import BaseModel, Field, model_validator

VERCEL_DEPLOYMENT_ID_RE = re.compile(r"(dpl_[a-zA-Z0-9]+)")


class DashboardTriggerRequest(BaseModel):
    """Dashboard trigger — NL query and/or pasted Vercel deployment link."""

    source: str = "dashboard"
    query: str = ""
    incident_id: str | None = None
    vercel_url: str | None = Field(
        default=None,
        description="Vercel deployment URL or raw dpl_… id from the dashboard.",
    )
    context: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_query_or_vercel(self) -> "DashboardTriggerRequest":
        if not self.query.strip() and not self.vercel_url:
            raise ValueError("Provide a natural-language query and/or a Vercel deployment URL.")
        return self


def extract_vercel_deployment_id(value: str | None) -> str | None:
    if not value:
        return None
    match = VERCEL_DEPLOYMENT_ID_RE.search(value.strip())
    return match.group(1) if match else None


def _dig(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def parse_sentry_webhook(payload: dict[str, Any]) -> dict[str, str]:
    """Extract normalized context from Sentry issue or alert webhook payloads."""
    issue = _dig(payload, "data", "issue") or payload.get("issue") or {}
    if not isinstance(issue, dict):
        issue = {}

    event = _dig(payload, "data", "event") or payload.get("event") or {}
    if not isinstance(event, dict):
        event = {}

    project = issue.get("project") or event.get("project") or payload.get("project") or {}
    if isinstance(project, dict):
        project_slug = str(project.get("slug") or project.get("name") or "")
    else:
        project_slug = str(project or "")

    issue_id = str(issue.get("id") or event.get("issue_id") or payload.get("issue_id") or "")
    short_id = str(issue.get("shortId") or issue.get("short_id") or payload.get("short_id") or "")
    title = str(
        issue.get("title")
        or event.get("title")
        or _dig(event, "metadata", "title")
        or payload.get("title")
        or ""
    )
    level = str(issue.get("level") or event.get("level") or payload.get("level") or "error")

    sentry_org_slug = ""
    for key in ("organization", "installation"):
        block = payload.get(key)
        if isinstance(block, dict) and block.get("slug"):
            sentry_org_slug = str(block["slug"]).strip()
            break
    if not sentry_org_slug and isinstance(payload.get("organization"), str):
        sentry_org_slug = str(payload["organization"]).strip()

    context: dict[str, str] = {
        "trigger_type": "sentry_webhook",
        "sentry_issue_id": issue_id,
        "sentry_short_id": short_id,
        "sentry_project": project_slug,
        "sentry_level": level,
        "sentry_title": title,
        "sentry_org_slug": sentry_org_slug,
    }
    return {k: v for k, v in context.items() if v}


def build_sentry_query(context: dict[str, str]) -> str:
    label = context.get("sentry_short_id") or context.get("sentry_issue_id") or "unknown issue"
    project = context.get("sentry_project") or "unknown project"
    title = context.get("sentry_title") or "production error"
    level = context.get("sentry_level") or "error"
    return (
        f"Investigate Sentry {level} {label} on project {project}: {title}. "
        "Correlate with recent deploys, PRs, and incident channel context."
    )


def normalize_dashboard(payload: DashboardTriggerRequest) -> "TriggerRequest":
    from app.schemas.trigger import TriggerRequest

    context = dict(payload.context)
    deployment_id = extract_vercel_deployment_id(payload.vercel_url)
    if deployment_id:
        context["vercel_deployment_id"] = deployment_id
        context["trigger_type"] = "vercel_deployment"
        if payload.vercel_url:
            context["vercel_url"] = payload.vercel_url.strip()

    if payload.incident_id:
        raw_incident = payload.incident_id.strip()
        context["incident_ref"] = raw_incident
        # Sentry Coral issues.id is numeric — ignore event UUIDs / hashes from the UI.
        if raw_incident.isdigit() and not context.get("sentry_issue_id"):
            context["sentry_issue_id"] = raw_incident

    query = payload.query.strip()
    if not query and deployment_id:
        query = (
            f"Investigate failures for Vercel deployment {deployment_id}. "
            "Find correlated Sentry errors, recent PRs, and ownership."
        )
    elif not query:
        query = "Investigate the reported production incident."

    return TriggerRequest(
        source="dashboard",
        incident_id=payload.incident_id or context.get("sentry_short_id"),
        query=query,
        context=context,
    )


def normalize_sentry_webhook(payload: dict[str, Any]) -> "TriggerRequest":
    from app.schemas.trigger import TriggerRequest

    context = parse_sentry_webhook(payload)
    issue_id = context.get("sentry_issue_id")
    short_id = context.get("sentry_short_id")

    return TriggerRequest(
        source="webhook",
        incident_id=short_id or issue_id,
        query=build_sentry_query(context),
        context=context,
    )
