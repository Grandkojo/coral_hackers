import json

from app.clients.openai_client import LLMClientError, OpenAIClient
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.investigation import InvestigationState, QueryPlan
from app.services.template_planner_service import TemplatePlannerService

logger = get_logger(__name__)

_CORAL_SCHEMA_HINT = """
Available Coral tables (read-only SELECT only):
- coral.tables(schema_name, table_name, description)
- github.pulls(owner, repo, number, title, state, merged_at, user__login, ...)
- github.collaborators(owner, repo, login, permissions__admin, permissions__push, html_url)
- github.teams(org, name, slug, description, html_url)
- sentry.issues(id, title, level, first_seen, count, user_count, project, ...)
- slack.channels(name, purpose, topic, id)
- vercel.deployments(uid, name, project_id, state, target, creator__username, created_at)
- vercel.projects(id, name, framework, link) — link JSON: json_get_str(link, 'org'), json_get_str(link, 'repo')

Rules:
- Only output read-only SQL starting with SELECT or WITH.
- Prefer cross-source JOINs when correlating deploys, PRs, and Sentry issues.
- Use trigger context filters when provided (github_owner, github_repo, sentry_issue_id, vercel_deployment_id).
- Always include LIMIT (max 50).
- Return JSON: {"sql": "...", "rationale": "..."}.
"""


class LLMPlannerService:
    """Uses an LLM to plan the next Coral SQL query from NL + investigation state."""

    def __init__(
        self,
        llm_client: OpenAIClient | None = None,
        template_planner: TemplatePlannerService | None = None,
    ) -> None:
        self._llm = llm_client or OpenAIClient()
        self._template = template_planner or TemplatePlannerService()

    @property
    def enabled(self) -> bool:
        return self._llm.enabled

    def plan_next_query(self, state: InvestigationState, user_query: str) -> QueryPlan:
        if not self.enabled:
            return self._template.plan_next_query(state, user_query)

        # First iteration: schema discovery is reliable via template.
        if state.iteration_count == 0:
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
    for plan in state.query_plans[-3:]:
        prior.append(
            {
                "iteration": plan.iteration,
                "rationale": plan.rationale,
                "sql_preview": plan.sql[:240],
            }
        )

    evidence_preview = state.evidence_rows[:5]
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
            "instruction": (
                "Plan the single best next Coral SQL query to progress this "
                "production incident investigation."
            ),
        },
        indent=2,
    )
