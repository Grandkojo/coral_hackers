import httpx

from app.clients.llm_client import LLMClientError
from app.clients.llm_json import parse_json_content
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
_DEFAULT_MODEL = "claude-sonnet-4-20250514"


class AnthropicClient:
    """Legacy paid Anthropic API — not used by default (see Gemini/Groq in llm_factory)."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else settings.anthropic_api_key
        self._model = (model or settings.resolved_planner_model()).strip() or _DEFAULT_MODEL

    @property
    def enabled(self) -> bool:
        return bool(self._api_key.strip())

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.enabled:
            raise LLMClientError("Anthropic API key is not configured.")

        system = (
            f"{system_prompt.strip()}\n\n"
            "Respond with a single JSON object only (no markdown fences)."
        )

        try:
            response = httpx.post(
                _ANTHROPIC_MESSAGES_URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": _ANTHROPIC_VERSION,
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": 2048,
                    "temperature": 0.2,
                    "system": system,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=60.0,
            )
        except httpx.HTTPError as exc:
            raise LLMClientError(f"Anthropic request failed: {exc}") from exc

        if response.status_code != 200:
            raise LLMClientError(
                f"Anthropic error {response.status_code}: {response.text[:300]}"
            )

        try:
            payload = response.json()
            blocks = payload["content"]
            text = next(
                block["text"]
                for block in blocks
                if block.get("type") == "text" and block.get("text")
            )
        except (KeyError, IndexError, StopIteration, TypeError) as exc:
            raise LLMClientError("Unexpected Anthropic response shape.") from exc

        return parse_json_content(text)
