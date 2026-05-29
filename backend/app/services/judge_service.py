from app.clients.llm_factory import create_llm_client
from app.core.config import settings
from app.schemas.investigation import InvestigationState
from app.services.llm_judge_service import LLMJudgeService
from app.services.rules_judge_service import RulesJudgeService


class JudgeService:
    """Facade: LLM judge (cheaper model) when configured, else rules-based judge."""

    def __init__(self) -> None:
        self._rules = RulesJudgeService()
        llm_client = create_llm_client(
            settings.resolved_judge_model(),
            role="judge",
        )
        self._llm = (
            LLMJudgeService(llm_client=llm_client, rules_judge=self._rules)
            if llm_client is not None
            else None
        )
        self._user_query = ""

    @property
    def mode(self) -> str:
        if self._llm is not None and self._llm.enabled:
            return f"llm:{settings.resolved_judge_llm_provider().value}"
        return "rules"

    def set_user_query(self, user_query: str) -> None:
        self._user_query = user_query

    def update_state(self, state: InvestigationState, rows: list[dict]) -> None:
        if self._llm is not None and self._llm.enabled:
            self._llm.update_state(state, rows, user_query=self._user_query)
            return
        self._rules.update_state(state, rows)

    def has_sufficient_evidence(self, state: InvestigationState) -> bool:
        if self._llm is not None and self._llm.enabled:
            return self._llm.has_sufficient_evidence(state)
        return self._rules.has_sufficient_evidence(state)

    def determine_root_cause(self, state: InvestigationState) -> str | None:
        if self._llm is not None and self._llm.enabled:
            return self._llm.determine_root_cause(state)
        return self._rules.determine_root_cause(state)
