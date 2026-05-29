import httpx

from app.clients.llm_client import LLMClientError
from app.clients.llm_json import parse_json_content
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIClient:
    """Legacy paid OpenAI API — not used by default (see Gemini/Groq in llm_factory)."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else settings.openai_api_key
        resolved = (model or settings.resolved_planner_model()).strip()
        self._model = resolved or _DEFAULT_MODEL

    @property
    def enabled(self) -> bool:
        return bool(self._api_key.strip())

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.enabled:
            raise LLMClientError("OpenAI API key is not configured.")

        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=60.0,
            )
        except httpx.HTTPError as exc:
            raise LLMClientError(f"OpenAI request failed: {exc}") from exc

        if response.status_code != 200:
            raise LLMClientError(
                f"OpenAI error {response.status_code}: {response.text[:300]}"
            )

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMClientError("Unexpected OpenAI response shape.") from exc

        return parse_json_content(content)
