from app.clients.llm_factory import create_llm_client
from app.core.config import settings
from app.schemas.investigation import InvestigationState, QueryPlan
from app.services.llm_planner_service import LLMPlannerService
from app.services.template_planner_service import TemplatePlannerService


class PlannerService:
    """Facade: Gemini/Groq planner when configured, else template planner."""

    def __init__(self) -> None:
        self._template = TemplatePlannerService()
        self._llm_client = create_llm_client(
            settings.resolved_planner_model(),
            role="planner",
        )
        self._llm = (
            LLMPlannerService(llm_client=self._llm_client, template_planner=self._template)
            if self._llm_client is not None
            else None
        )

    @property
    def mode(self) -> str:
        if self._llm is not None and self._llm.enabled:
            return f"llm:{settings.resolved_planner_llm_provider().value}"
        return "template"

    def plan_next_query(self, state: InvestigationState, user_query: str) -> QueryPlan:
        if self._llm is not None and self._llm.enabled:
            return self._llm.plan_next_query(state, user_query)
        return self._template.plan_next_query(state, user_query)
