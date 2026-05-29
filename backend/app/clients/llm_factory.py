from typing import Literal

from app.clients.gemini_client import GeminiClient
from app.clients.groq_client import GroqClient
from app.clients.llm_client import PlannerLLMClient
from app.core.config import LlmProvider, settings
from app.core.logging import get_logger

logger = get_logger(__name__)

LlmRole = Literal["planner", "judge"]


def create_llm_client(model: str, *, role: LlmRole) -> PlannerLLMClient | None:
    """Build planner or judge LLM client from free-tier Gemini / Groq by default."""
    provider = (
        settings.resolved_judge_llm_provider()
        if role == "judge"
        else settings.resolved_planner_llm_provider()
    )

    if provider == LlmProvider.gemini:
        client = GeminiClient(model=model)
        if client.enabled:
            return client
        logger.debug("planner/judge provider=gemini but GEMINI_API_KEY is empty")
        return None

    client = GroqClient(model=model)
    if client.enabled:
        return client
    logger.debug("planner/judge provider=groq but GROQ_API_KEY is empty")
    return None
