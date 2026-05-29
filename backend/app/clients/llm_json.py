import json
import re

from app.clients.llm_client import LLMClientError


def parse_json_content(content: str) -> dict:
    text = content.strip()
    fence = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMClientError(f"Could not parse LLM JSON: {content[:200]}") from exc

    if not isinstance(parsed, dict):
        raise LLMClientError("LLM response must be a JSON object.")
    return parsed
