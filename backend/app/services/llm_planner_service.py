import json

from app.clients.llm_client import LLMClientError, PlannerLLMClient
from app.clients.llm_factory import create_llm_client
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.investigation import InvestigationState, QueryPlan
from app.services.github_query_budget import github_rate_limited_from_context
from app.services.template_planner_service import (
    TemplatePlannerService,
    context_anchored_plan,
)
from app.services.trigger_discovery import should_skip_schema_catalog

logger = get_logger(__name__)

_CORAL_SCHEMA_HINT = """
Available Coral tables (read-only SELECT only):
- coral.tables(schema_name, table_name, description)
- github.pulls(owner, repo, number, title, state, merged_at, user__login, ...)
- github.collaborators(owner, repo, login, permissions__admin, permissions__push, html_url)
- github.teams(org, name, slug, description, html_url)
- sentry.issues(id, title, level, first_seen, count, user_count, project, ...)
  IMPORTANT: sentry.issues.project is the Sentry project slug (often ends with -api),
  NOT the GitHub repo name. Do not equate project to github_repo.
- slack.channels(name, purpose, topic, id)
- vercel.deployments(uid, name, project_id, state, target, creator__username, created_at)
- vercel.projects(id, name, framework, link) — link JSON: json_get_str(link, 'org'), json_get_str(link, 'repo')

Rules:
- Only output read-only SQL starting with SELECT or WITH.
- Prefer cross-source JOINs when correlating deploys, PRs, and Sentry issues.
- Use trigger context filters when provided (github_owner, github_repo, sentry_issue_id, vercel_deployment_id).
- HTTP 500 reports often appear in Sentry as TypeError/Exception titles — filter by level/error and time, not only title ILIKE '%500%'.
- If a query returns 0 rows, simplify: query sentry.issues and vercel.deployments separately before complex CTE joins.
- Do not subtract INTERVAL from timestamp strings (e.g. `created_at >= '...Z' - INTERVAL '1 day'` fails in Coral).
  Use `s.first_seen >= d.created_at` joins and `ORDER BY d.created_at DESC` instead.
- Always include LIMIT (max 50).
- Return JSON: {"sql": "...", "rationale": "..."}.
"""


class LLMPlannerService:
    """Uses an LLM to plan the next Coral SQL query from NL + investigation state."""

    def __init__(
        self,
        llm_client: PlannerLLMClient | None = None,
        template_planner: TemplatePlannerService | None = None,
    ) -> None:
        self._llm = llm_client or create_llm_client(
            settings.resolved_planner_model(),
            role="planner",
        )
        self._template = template_planner or TemplatePlannerService()

    @property
    def enabled(self) -> bool:
        return self._llm is not None and self._llm.enabled

    def plan_next_query(self, state: InvestigationState, user_query: str) -> QueryPlan:
        if not self.enabled or self._llm is None:
            return self._template.plan_next_query(state, user_query)

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

        # Schema discovery only when no deploy/Sentry/repo anchors to run first.
        if state.iteration_count == 0 and not should_skip_schema_catalog(
            state.trigger_context
        ):
            return self._template.plan_next_query(state, user_query)

        # Prior query returned nothing — do not let the LLM guess harder.
        if state.last_query_row_count == 0:
            logger.info(
                "planner: last query returned 0 rows at iter=%d; using template",
                state.iteration_count,
            )
            return self._template.plan_next_query(state, user_query)

        try:
            payload = self._llm.complete_json(
                system_prompt=_CORAL_SCHEMA_HINT,
                user_prompt=_build_user_prompt(state, user_query),
            )
            sql = str(payload.get("sql", "")).strip()
            rationale = str(payload.get("rationale", "")).strip()
            if not sql or not rationale:
                raise LLMClientError("LLM response missing sql or rationale.")
            return QueryPlan(
                sql=sql,
                rationale=rationale,
                iteration=state.iteration_count,
            )
        except LLMClientError as exc:
            logger.warning(
                "llm planner fallback at iter=%d: %s",
                state.iteration_count,
                exc,
            )
            return self._template.plan_next_query(state, user_query)


def _build_user_prompt(state: InvestigationState, user_query: str) -> str:
    prior = []
    counts = state.query_row_counts
    for idx, plan in enumerate(state.query_plans[-3:]):
        count_idx = len(counts) - len(state.query_plans[-3:]) + idx
        row_count = counts[count_idx] if 0 <= count_idx < len(counts) else None
        prior.append(
            {
                "iteration": plan.iteration,
                "rationale": plan.rationale,
                "sql_preview": plan.sql[:240],
                "row_count": row_count,
            }
        )

    # Prefer recent investigative rows over schema-catalog noise from iter 0.
    evidence_preview = [
        row
        for row in reversed(state.evidence_rows)
        if row.get("schema_name") is None
    ][:8]
    if not evidence_preview:
        evidence_preview = state.evidence_rows[-8:]

    instruction = (
        "Plan the single best next Coral SQL query to progress this "
        "production incident investigation."
    )
    if state.last_query_row_count == 0:
        instruction += (
            " The previous query returned 0 rows — simplify: query one table "
            "at a time (sentry.issues by id or time, vercel.deployments by uid), "
            "avoid title ILIKE '%500%', and never equate sentry.project to github repo."
        )

    return json.dumps(
        {
            "user_query": user_query,
            "iteration": state.iteration_count,
            "max_iterations": settings.max_investigation_iterations,
            "trigger_context": state.trigger_context,
            "confidence_score": state.confidence_score,
            "hypotheses": [h.text for h in state.hypotheses[:5]],
            "prior_queries": prior,
            "recent_evidence_rows": evidence_preview,
            "instruction": instruction,
        },
        indent=2,
    )
