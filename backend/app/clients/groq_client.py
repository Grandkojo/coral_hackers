import httpx

from app.clients.llm_client import LLMClientError
from app.clients.llm_json import parse_json_content
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
_DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqClient:
    """Groq OpenAI-compatible chat API (free tier at console.groq.com)."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else settings.groq_api_key
        self._model = (model or _DEFAULT_MODEL).strip() or _DEFAULT_MODEL

    @property
    def enabled(self) -> bool:
        return bool(self._api_key.strip())

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.enabled:
            raise LLMClientError("GROQ_API_KEY is not configured.")

        try:
            response = httpx.post(
                _GROQ_CHAT_URL,
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
            raise LLMClientError(f"Groq request failed: {exc}") from exc

        if response.status_code != 200:
            raise LLMClientError(
                f"Groq error {response.status_code}: {response.text[:300]}"
            )

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMClientError("Unexpected Groq response shape.") from exc

        return parse_json_content(content)
