from app.core.config import GitHubAccountType, settings
from app.schemas.investigation import InvestigationState, QueryPlan

# ---------------------------------------------------------------------------
# Curated investigation query templates (real Coral table/column names)
# Context from triggers overrides static .env defaults where available.
# ---------------------------------------------------------------------------


def _github_target(context: dict[str, str]) -> tuple[str, str]:
    owner = context.get("github_owner") or settings.github_owner or "Grandkojo"
    repo = context.get("github_repo") or settings.github_repo or "coral_hackers"
    return owner, repo


def _ownership_sql(owner: str, repo: str) -> tuple[str, str]:
    if settings.github_account_type == GitHubAccountType.org:
        return (
            f"""SELECT
  name        AS service,
  slug        AS team,
  description AS oncall,
  html_url    AS slack_channel,
  org         AS repo
FROM github.teams
WHERE org = '{owner}'
LIMIT 20""",
            "Identify GitHub org teams for remediation routing.",
        )

    return (
        f"""SELECT
  repo        AS service,
  login       AS team,
  login       AS oncall,
  html_url    AS slack_channel,
  owner       AS repo
FROM github.collaborators
WHERE owner = '{owner}'
  AND repo = '{repo}'
ORDER BY permissions__admin DESC, permissions__push DESC, login
LIMIT 20""",
        "Identify repo collaborators for personal-account remediation routing.",
    )


def _sentry_issue_filter(context: dict[str, str]) -> str:
    issue_id = context.get("sentry_issue_id")
    if issue_id:
        return f"  AND s.id = '{issue_id}'"
    return ""


def _vercel_deployments_sql(context: dict[str, str]) -> tuple[str, str]:
    deployment_id = context.get("vercel_deployment_id")
    if deployment_id:
        return (
            f"""SELECT
  uid,
  name,
  project_id,
  state,
  target,
  creator__username,
  created_at
FROM vercel.deployments
WHERE uid = '{deployment_id}'
LIMIT 5""",
            f"Inspect triggered Vercel deployment {deployment_id}.",
        )

    return (
        """SELECT
  uid,
  name,
  project_id,
  state,
  target,
  creator__username,
  created_at
FROM vercel.deployments
ORDER BY created_at DESC
LIMIT 10""",
        "Retrieve recent deployment history to correlate deploy timestamps with error spikes.",
    )


def build_plans(context: dict[str, str] | None = None) -> list[QueryPlan]:
    ctx = context or {}
    owner, repo = _github_target(ctx)
    slack_channel = settings.slack_incident_channel or "incidents"
    ownership_sql, ownership_rationale = _ownership_sql(owner, repo)
    vercel_sql, vercel_rationale = _vercel_deployments_sql(ctx)
    sentry_filter = _sentry_issue_filter(ctx)

    return [
        QueryPlan(
            sql=(
                "SELECT schema_name, table_name, description "
                "FROM coral.tables "
                "ORDER BY schema_name "
                "LIMIT 50"
            ),
            rationale=(
                "Discover available Coral sources and tables before forming "
                "investigation queries."
            ),
            iteration=0,
        ),
        QueryPlan(
            sql=f"""SELECT
  g.title        AS pr_title,
  g.number       AS pr_number,
  g.user__login  AS pr_author,
  g.merged_at,
  s.title        AS error_message,
  s.level        AS error_level,
  s.first_seen,
  s.count        AS times_seen,
  s.user_count   AS affected_users,
  s.id           AS sentry_issue_id
FROM github.pulls g
JOIN sentry.issues s
  ON s.first_seen >= g.merged_at
WHERE g.owner = '{owner}'
  AND g.repo = '{repo}'
  AND s.level IN ('fatal', 'error')
  AND g.state = 'closed'
{sentry_filter}
ORDER BY s.first_seen DESC
LIMIT 20""",
            rationale=(
                "Correlate recent PRs merged before fatal/error Sentry events "
                "to identify regression candidates."
            ),
            iteration=1,
        ),
        QueryPlan(
            sql=f"""SELECT
  purpose AS text,
  name    AS channel,
  topic   AS user,
  id      AS ts
FROM slack.channels
WHERE name = '{slack_channel}'
LIMIT 50""",
            rationale=(
                "Pull incident channel metadata while message history is "
                "unavailable in this Coral slack source version."
            ),
            iteration=2,
        ),
        QueryPlan(
            sql=vercel_sql,
            rationale=vercel_rationale,
            iteration=3,
        ),
        QueryPlan(
            sql=ownership_sql,
            rationale=ownership_rationale,
            iteration=4,
        ),
    ]


class TemplatePlannerService:
    """Template-based planner: maps iteration index to a curated Coral query."""

    def plan_next_query(self, state: InvestigationState, user_query: str) -> QueryPlan:
        plans = build_plans(state.trigger_context)
        idx = min(state.iteration_count, len(plans) - 1)
        template = plans[idx]
        return QueryPlan(
            sql=template.sql,
            rationale=template.rationale,
            iteration=state.iteration_count,
        )
