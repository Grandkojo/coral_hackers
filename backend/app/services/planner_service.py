from app.schemas.investigation import InvestigationState, QueryPlan

# ---------------------------------------------------------------------------
# Curated investigation query templates
# Iteration 0 — catalog probe (always first)
# Iteration 1 — deploy↔error correlation (core Coral JOIN)
# Iteration 2 — Slack incident context
# Iteration 3 — deployment timeline from Vercel
# Iteration 4 — ownership lookup
# ---------------------------------------------------------------------------

_PLANS: list[QueryPlan] = [
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
        sql="""SELECT
  g.title        AS pr_title,
  g.number       AS pr_number,
  g.user_login   AS pr_author,
  g.merged_at,
  s.message      AS error_message,
  s.level        AS error_level,
  s.first_seen,
  s.times_seen,
  s.affected_users,
  s.id           AS sentry_issue_id
FROM github.pull_requests g
JOIN sentry.issues s
  ON s.first_seen >= g.merged_at
WHERE s.level IN ('fatal', 'error')
  AND g.state = 'closed'
ORDER BY s.first_seen DESC
LIMIT 20""",
        rationale=(
            "Correlate recent PRs merged before fatal/error Sentry events "
            "to identify regression candidates."
        ),
        iteration=1,
    ),
    QueryPlan(
        sql="""SELECT
  text,
  user,
  channel,
  ts
FROM slack.messages
WHERE channel = '#incidents'
ORDER BY ts DESC
LIMIT 50""",
        rationale=(
            "Pull recent incident channel messages to surface team context, "
            "manual observations, and remediation actions."
        ),
        iteration=2,
    ),
    QueryPlan(
        sql="""SELECT
  deployment_id,
  project,
  branch,
  commit_sha,
  triggered_by,
  state,
  created_at
FROM vercel.deployments
ORDER BY created_at DESC
LIMIT 10""",
        rationale=(
            "Retrieve deployment history to correlate deploy timestamps "
            "with error spikes."
        ),
        iteration=3,
    ),
    QueryPlan(
        sql="""SELECT
  service,
  team,
  oncall,
  slack_channel,
  repo
FROM github.codeowners
LIMIT 20""",
        rationale=(
            "Identify service ownership so the severity gate can route "
            "human-paired remediations to the right team."
        ),
        iteration=4,
    ),
]


class PlannerService:
    """Template-based planner: maps iteration index to a curated Coral query."""

    def plan_next_query(self, state: InvestigationState, user_query: str) -> QueryPlan:
        idx = min(state.iteration_count, len(_PLANS) - 1)
        template = _PLANS[idx]
        return QueryPlan(
            sql=template.sql,
            rationale=template.rationale,
            iteration=state.iteration_count,
        )
