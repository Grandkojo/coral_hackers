from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.org_context import OrgContext
from app.schemas.report import ReportResponse
from app.clients.slack_client import SlackClient

logger = get_logger(__name__)


def _report_url(org_context: OrgContext | None, investigation_id: str) -> str | None:
    base = settings.frontend_base_url.strip().rstrip("/")
    if not base:
        return None
    slug = org_context.organization_slug if org_context else ""
    if slug and slug != "legacy":
        return f"{base}/{slug}/report/{investigation_id}"
    return f"{base}/report/{investigation_id}"


def format_sentry_slack_message(
    report: ReportResponse,
    *,
    org_context: OrgContext | None,
    sentry_short_id: str = "",
    sentry_title: str = "",
) -> str:
    issue_label = sentry_short_id or "Sentry issue"
    title_line = f" — {sentry_title}" if sentry_title else ""
    root = (report.root_cause or "Investigation complete — see report for evidence.").strip()
    if len(root) > 500:
        root = root[:497] + "..."

    lines = [
        ":mag: *Reef investigation complete*",
        f"• Issue: `{issue_label}`{title_line}",
        f"• Severity: `{report.severity_score:.2f}` · {report.remediation_mode.replace('_', ' ')}",
        f"• Root cause: {root}",
    ]
    if report.unresolved_gaps:
        lines.append(f"• Gaps: {report.unresolved_gaps[0]}")

    url = _report_url(org_context, report.investigation_id)
    if url:
        lines.append(f"• <{url}|Open full report>")

    if report.remediation_mode == "human_agent_paired":
        lines.append(
            f"\n_Human approval required — use dashboard or "
            f"`/reef approve {report.investigation_id}` when wired._"
        )
    return "\n".join(lines)


async def notify_sentry_investigation_complete(
    report: ReportResponse,
    *,
    org_context: OrgContext | None,
    sentry_short_id: str = "",
    sentry_title: str = "",
) -> None:
    token = ""
    channel = settings.slack_incident_channel or "incidents"
    if org_context is not None:
        token = org_context.slack_token or settings.slack_bot_token
        channel = org_context.slack_incident_channel or channel
    else:
        token = settings.slack_bot_token

    text = format_sentry_slack_message(
        report,
        org_context=org_context,
        sentry_short_id=sentry_short_id,
        sentry_title=sentry_title,
    )
    client = SlackClient(token=token)
    result = await client.post_message(channel, text)
    if not result.get("ok"):
        logger.warning(
            "slack notify failed channel=%s error=%s",
            channel,
            result.get("error"),
        )
