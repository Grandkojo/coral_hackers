from app.core.config import settings
from app.schemas.investigation import InvestigationState, QueryPlan
from app.services.llm_planner_service import LLMPlannerService
from app.services.template_planner_service import TemplatePlannerService


class PlannerService:
    """Facade: LLM planner when OPENAI_API_KEY is set, else template planner."""

    def __init__(self) -> None:
        self._template = TemplatePlannerService()
        self._llm = LLMPlannerService(template_planner=self._template)

    @property
    def mode(self) -> str:
        return "llm" if settings.openai_api_key.strip() else "template"

    def plan_next_query(self, state: InvestigationState, user_query: str) -> QueryPlan:
        if settings.openai_api_key.strip():
            return self._llm.plan_next_query(state, user_query)
        return self._template.plan_next_query(state, user_query)
