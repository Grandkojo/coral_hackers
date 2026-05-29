"""Promote Coral row fields into trigger_context for later planner iterations."""

from __future__ import annotations

import re

from app.core.logging import get_logger

logger = get_logger(__name__)

_NUMERIC_SENTRY_RE = re.compile(r"^\d+$")


def _numeric_sentry_id(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if _NUMERIC_SENTRY_RE.match(text) else None


def apply_discovered_context(
    context: dict[str, str], rows: list[dict]
) -> dict[str, str]:
    """After each query, persist discovered Sentry/deploy ids for anchored follow-ups."""
    if not rows:
        return context

    updated = dict(context)
    best_sentry: tuple[str, str, str] | None = None  # (first_seen, id, title)

    for row in rows:
        sid = _numeric_sentry_id(
            row.get("sentry_issue_id") or row.get("id") or row.get("issue_id")
        )
        if sid:
            title = str(row.get("error_message") or row.get("title") or "")
            first_seen = str(row.get("first_seen") or "")
            candidate = (first_seen, sid, title)
            if best_sentry is None or candidate[0] > best_sentry[0]:
                best_sentry = candidate

        deploy = row.get("deployment_id") or row.get("uid")
        if deploy and not updated.get("vercel_deployment_id"):
            updated["vercel_deployment_id"] = str(deploy)
        deploy_at = row.get("deploy_at") or row.get("created_at")
        if deploy_at and not updated.get("vercel_deploy_at"):
            updated["vercel_deploy_at"] = str(deploy_at)

    if best_sentry:
        _, sid, title = best_sentry
        updated["sentry_issue_id"] = sid
        if title:
            updated["sentry_title"] = title[:200]
        if best_sentry[0]:
            updated["sentry_first_seen"] = best_sentry[0]

    if updated.get("sentry_issue_id") and updated is not context:
        logger.info(
            "discovered sentry_issue_id=%s for deployment=%s",
            updated.get("sentry_issue_id"),
            updated.get("vercel_deployment_id"),
        )
    return updated


def should_skip_schema_catalog(context: dict[str, str]) -> bool:
    """Skip coral.tables when we can run anchored incident queries immediately."""
    if context.get("vercel_deployment_id"):
        return True
    if _numeric_sentry_id(context.get("sentry_issue_id")):
        return True
    return bool(context.get("github_owner") and context.get("github_repo"))
