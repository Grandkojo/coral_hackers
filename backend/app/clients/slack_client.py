import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_BASE_URL = "https://slack.com/api"


class SlackClient:
    """Slack API client — used on the remediation/notification path only.

    Investigation reads go through Coral (slack.messages table), not here.
    """

    def __init__(self) -> None:
        self._token = settings.slack_bot_token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def post_message(self, channel_id: str, text: str) -> dict:
        if not self._token:
            logger.warning("SLACK_BOT_TOKEN not set; skipping post_message")
            return {"ok": False, "error": "token_not_configured"}
        async with httpx.AsyncClient(base_url=_BASE_URL, timeout=10.0) as client:
            response = await client.post(
                "/chat.postMessage",
                headers=self._headers(),
                json={"channel": channel_id, "text": text},
            )
            response.raise_for_status()
            return response.json()

    async def fetch_incident_threads(self, channel_id: str) -> list[dict]:
        if not self._token:
            return []
        async with httpx.AsyncClient(base_url=_BASE_URL, timeout=10.0) as client:
            response = await client.get(
                "/conversations.history",
                headers=self._headers(),
                params={"channel": channel_id, "limit": 50},
            )
            response.raise_for_status()
            return response.json().get("messages", [])

    async def request_approval(
        self,
        channel_id: str,
        investigation_id: str,
        root_cause: str,
        severity_score: float,
    ) -> dict:
        message = (
            f":rotating_light: *High-severity incident — human approval required*\n"
            f"• Investigation: `{investigation_id}`\n"
            f"• Severity score: `{severity_score:.2f}`\n"
            f"• Root cause: {root_cause}\n\n"
            f"Reply `/reef approve {investigation_id}` to proceed with "
            f"autonomous remediation."
        )
        return await self.post_message(channel_id, message)
