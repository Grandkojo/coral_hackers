import httpx

from app.clients.llm_client import LLMClientError
from app.clients.llm_json import parse_json_content
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiClient:
    """Google AI Studio Gemini API (free tier at aistudio.google.com)."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else settings.gemini_api_key
        self._model = (model or _DEFAULT_MODEL).strip() or _DEFAULT_MODEL

    @property
    def enabled(self) -> bool:
        return bool(self._api_key.strip())

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.enabled:
            raise LLMClientError("GEMINI_API_KEY is not configured.")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent"
        )

        try:
            response = httpx.post(
                url,
                params={"key": self._api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "systemInstruction": {
                        "parts": [{"text": system_prompt.strip()}],
                    },
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": user_prompt}],
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.2,
                        "responseMimeType": "application/json",
                        "thinkingConfig": {"thinkingBudget": 0},
                    },
                },
                timeout=60.0,
            )
        except httpx.HTTPError as exc:
            raise LLMClientError(f"Gemini request failed: {exc}") from exc

        if response.status_code != 200:
            raise LLMClientError(
                f"Gemini error {response.status_code}: {response.text[:300]}"
            )

        try:
            payload = response.json()
            parts = payload["candidates"][0]["content"]["parts"]
            text = next(
                part["text"]
                for part in parts
                if isinstance(part.get("text"), str) and part["text"].strip()
            )
        except (KeyError, IndexError, StopIteration, TypeError) as exc:
            raise LLMClientError("Unexpected Gemini response shape.") from exc

        return parse_json_content(text)
