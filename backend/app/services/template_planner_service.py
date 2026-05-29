from app.core.config import GitHubAccountType, settings
from app.schemas.investigation import InvestigationState, QueryPlan
from app.services.github_query_budget import (
    github_rate_limited_from_context,
    touches_github_data,
)
from app.services.trigger_discovery import should_skip_schema_catalog

# ---------------------------------------------------------------------------
# Curated investigation query templates (real Coral table/column names)
# Context from triggers overrides static .env defaults where available.
# ---------------------------------------------------------------------------


def _github_target(context: dict[str, str]) -> tuple[str, str]:
    owner = (
        context.get("github_owner")
        or settings.github_owner
        or "Grandkojo"
    )
    repo = (
        context.get("github_repo")
        or settings.github_repo
        or "coral_hackers"
    )
    return owner, repo


def _github_account_type(context: dict[str, str]) -> GitHubAccountType:
    raw = context.get("github_account_type")
    if raw == GitHubAccountType.user.value:
        return GitHubAccountType.user
    if raw == GitHubAccountType.org.value:
        return GitHubAccountType.org
    return settings.github_account_type


def _ownership_sql(owner: str, repo: str, context: dict[str, str]) -> tuple[str, str]:
    if _github_account_type(context) == GitHubAccountType.org:
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


def _numeric_sentry_issue_id(context: dict[str, str]) -> str | None:
    raw = context.get("sentry_issue_id", "").strip()
    return raw if raw.isdigit() else None


def _discovery_iteration(context: dict[str, str]) -> int:
    """Iter 0 when skipping catalog; iter 1 when catalog ran first."""
    return 0 if should_skip_schema_catalog(context) else 1


def _latest_production_incident_sql(owner: str, repo: str) -> QueryPlan:
    return QueryPlan(
        sql=f"""SELECT
  d.uid            AS deployment_id,
  d.created_at     AS deploy_at,
  s.id             AS sentry_issue_id,
  s.title          AS error_message,
  s.level          AS error_level,
  s.first_seen,
  s.project        AS sentry_project
FROM vercel.deployments d
JOIN vercel.projects p ON p.id = d.project_id
JOIN sentry.issues s
  ON s.first_seen >= d.created_at
 AND s.level IN ('error', 'fatal')
WHERE json_get_str(p.link, 'org') = '{owner}'
  AND json_get_str(p.link, 'repo') = '{repo}'
  AND d.target = 'production'
ORDER BY d.created_at DESC, s.first_seen DESC
LIMIT 10""",
        rationale=(
            "No deploy or Sentry id in trigger — load the latest production "
            "deploy and the newest error-level issue that appeared after it."
        ),
        iteration=0,
    )


def context_anchored_plan(
    iteration: int, context: dict[str, str], *, skip_github: bool = False
) -> QueryPlan | None:
    """Deterministic high-signal queries when dashboard provides deploy/issue ids."""
    if skip_github:
        return None

    owner, repo = _github_target(context)
    sentry_id = _numeric_sentry_issue_id(context)
    deployment_id = context.get("vercel_deployment_id")
    discover = _discovery_iteration(context)
    correlate = discover + 1
    pr_iter = discover + 2

    if iteration == discover and sentry_id:
        return QueryPlan(
            sql=f"""SELECT
  id,
  title,
  level,
  first_seen,
  count,
  user_count,
  project
FROM sentry.issues
WHERE id = '{sentry_id}'
LIMIT 5""",
            rationale=(
                f"Load Sentry issue {sentry_id} by id (no title filters; "
                "TypeError titles rarely contain '500')."
            ),
            iteration=iteration,
        )

    if iteration == discover and deployment_id and not sentry_id:
        return QueryPlan(
            sql=f"""SELECT
  s.id             AS sentry_issue_id,
  s.title          AS error_message,
  s.level          AS error_level,
  s.first_seen,
  s.project        AS sentry_project,
  d.uid            AS deployment_id,
  d.created_at     AS deploy_at
FROM vercel.deployments d
JOIN sentry.issues s
  ON s.first_seen >= d.created_at
 AND s.level IN ('error', 'fatal')
WHERE d.uid = '{deployment_id}'
ORDER BY s.first_seen DESC
LIMIT 10""",
            rationale=(
                "No valid numeric Sentry issue id — load the newest error-level "
                "issue that first appeared after the triggered deployment."
            ),
            iteration=iteration,
        )

    if (
        iteration == discover
        and not deployment_id
        and not sentry_id
        and owner
        and repo
    ):
        plan = _latest_production_incident_sql(owner, repo)
        plan.iteration = iteration
        return plan

    if iteration == correlate and deployment_id and sentry_id:
        return QueryPlan(
            sql=f"""SELECT
  d.uid            AS deployment_id,
  d.created_at     AS deploy_at,
  s.id             AS sentry_issue_id,
  s.title          AS error_message,
  s.level          AS error_level,
  s.first_seen,
  s.project        AS sentry_project
FROM vercel.deployments d
JOIN sentry.issues s
  ON s.first_seen >= d.created_at
WHERE d.uid = '{deployment_id}'
  AND s.id = '{sentry_id}'
LIMIT 10""",
            rationale=(
                "Correlate the triggered Vercel deployment with the known "
                "Sentry issue by id and post-deploy timestamp."
            ),
            iteration=iteration,
        )

    if iteration == correlate and deployment_id and not sentry_id:
        return QueryPlan(
            sql=f"""SELECT
  g.number       AS pr_number,
  g.title        AS pr_title,
  g.user__login  AS pr_author,
  g.merged_at,
  d.uid          AS deployment_id,
  d.created_at   AS deploy_at
FROM vercel.deployments d
JOIN github.pulls g
  ON g.owner = '{owner}'
 AND g.repo = '{repo}'
 AND g.state = 'closed'
 AND g.merged_at >= d.created_at
 AND g.merged_at <= d.created_at + INTERVAL '4' HOUR
WHERE d.uid = '{deployment_id}'
ORDER BY g.merged_at DESC
LIMIT 10""",
            rationale=(
                "List PRs merged at or after the deployment (up to 4h later) — "
                "excludes older PRs that predate this deploy."
            ),
            iteration=iteration,
        )

    if iteration == pr_iter and deployment_id and sentry_id:
        return QueryPlan(
            sql=f"""SELECT
  g.number       AS pr_number,
  g.title        AS pr_title,
  g.user__login  AS pr_author,
  g.merged_at,
  d.uid          AS deployment_id,
  d.created_at   AS deploy_at
FROM vercel.deployments d
JOIN github.pulls g
  ON g.owner = '{owner}'
 AND g.repo = '{repo}'
 AND g.state = 'closed'
 AND g.merged_at >= d.created_at
 AND g.merged_at <= d.created_at + INTERVAL '4' HOUR
WHERE d.uid = '{deployment_id}'
ORDER BY g.merged_at DESC
LIMIT 10""",
            rationale=(
                "List PRs merged at or after the deployment (up to 4h later) — "
                "wave-3 env-only deploys may return zero rows (expected)."
            ),
            iteration=iteration,
        )

    return None


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
    ownership_sql, ownership_rationale = _ownership_sql(owner, repo, ctx)
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
        skip_github = state.github_rate_limited or github_rate_limited_from_context(
            state.trigger_context
        )
        anchored = context_anchored_plan(
            state.iteration_count,
            state.trigger_context,
            skip_github=skip_github,
        )
        if anchored is not None:
            return anchored

        if (
            state.iteration_count == 0
            and should_skip_schema_catalog(state.trigger_context)
        ):
            # Anchored path should have returned; avoid burning iter 0 on catalog.
            return QueryPlan(
                sql=(
                    "SELECT schema_name, table_name FROM coral.tables "
                    "WHERE schema_name IN ('sentry','vercel','github','slack') "
                    "LIMIT 20"
                ),
                rationale="Scoped Coral schema (deploy/Sentry anchors active).",
                iteration=0,
            )

        plans = build_plans(state.trigger_context)
        idx = min(state.iteration_count, len(plans) - 1)
        template = plans[idx]
        if skip_github and touches_github_data(template.sql):
            return QueryPlan(
                sql=(
                    "SELECT 'github_rate_limited' AS status "
                    "FROM coral.tables LIMIT 0"
                ),
                rationale=(
                    "Skipped GitHub query — API rate limit active; "
                    "using Sentry/Vercel evidence only."
                ),
                iteration=state.iteration_count,
            )
        return QueryPlan(
            sql=template.sql,
            rationale=template.rationale,
            iteration=state.iteration_count,
        )
