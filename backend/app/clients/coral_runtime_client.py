import json
import os
import subprocess

from app.core.config import CoralMode, settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Mock data — realistic "checkout failed after last deploy" scenario
# ---------------------------------------------------------------------------

_MOCK_TABLES = [
    {"schema": "github", "table": "pull_requests", "description": "Merged pull requests"},
    {"schema": "github", "table": "commits", "description": "Repository commits"},
    {"schema": "github", "table": "codeowners", "description": "Code ownership mappings"},
    {"schema": "sentry", "table": "issues", "description": "Error events and exceptions"},
    {"schema": "slack", "table": "messages", "description": "Channel messages"},
    {"schema": "vercel", "table": "deployments", "description": "Deployment records"},
]

_MOCK_DEPLOY_ERRORS = [
    {
        "pr_title": "feat: refactor checkout payment validation",
        "pr_number": 234,
        "pr_author": "diana.reyes",
        "merged_at": "2026-05-26T18:42:00Z",
        "error_message": "TypeError: Cannot read properties of undefined (reading 'amount')",
        "error_level": "fatal",
        "first_seen": "2026-05-26T18:47:23Z",
        "times_seen": 512,
        "affected_users": 87,
        "sentry_issue_id": "CHECKOUT-4821",
    },
    {
        "pr_title": "chore: bump stripe-sdk to 14.2.1",
        "pr_number": 233,
        "pr_author": "alex.osei",
        "merged_at": "2026-05-26T17:30:00Z",
        "error_message": "StripeInvalidRequestError: No such payment_intent",
        "error_level": "error",
        "first_seen": "2026-05-26T17:55:10Z",
        "times_seen": 204,
        "affected_users": 34,
        "sentry_issue_id": "STRIPE-0099",
    },
]

_MOCK_SLACK_MESSAGES = [
    {
        "text": ":rotating_light: Checkout errors spiking — 500s on /api/checkout/confirm",
        "user": "pagerbot",
        "channel": "#incidents",
        "ts": "2026-05-26T18:48:00Z",
    },
    {
        "text": "Seeing TypeError in Sentry — payment.amount is undefined after PR #234 merged",
        "user": "diana.reyes",
        "channel": "#incidents",
        "ts": "2026-05-26T18:52:00Z",
    },
    {
        "text": "PR #234 touched PaymentValidator.validate() — refactored amount extraction. Could be the culprit.",
        "user": "alex.osei",
        "channel": "#incidents",
        "ts": "2026-05-26T18:55:00Z",
    },
    {
        "text": "Rolling back PR #234 now — will redeploy once fixed",
        "user": "diana.reyes",
        "channel": "#incidents",
        "ts": "2026-05-26T19:02:00Z",
    },
]

_MOCK_DEPLOYMENTS = [
    {
        "deployment_id": "dpl_abc123",
        "project": "checkout-service",
        "branch": "main",
        "commit_sha": "a1b2c3d",
        "triggered_by": "diana.reyes",
        "state": "ready",
        "created_at": "2026-05-26T18:44:00Z",
    },
    {
        "deployment_id": "dpl_xyz789",
        "project": "checkout-service",
        "branch": "main",
        "commit_sha": "9z8y7x6",
        "triggered_by": "ci-bot",
        "state": "ready",
        "created_at": "2026-05-26T17:31:00Z",
    },
]

_MOCK_OWNERSHIP = [
    {
        "service": "checkout-service",
        "team": "payments-platform",
        "oncall": "diana.reyes",
        "slack_channel": "#payments-platform",
        "repo": "acme/checkout-service",
    }
]

_MOCK_GITHUB_LINK = [
    {
        "github_owner": "Grandkojo",
        "github_repo": "coral_hackers",
    }
]


def _mock_query(sql: str) -> list[dict]:
    s = sql.lower()
    if "coral.tables" in s:
        return _MOCK_TABLES
    if "sentry" in s and ("join" in s or "fatal" in s or "pull" in s):
        return _MOCK_DEPLOY_ERRORS
    if "sentry" in s:
        return _MOCK_DEPLOY_ERRORS
    if "slack" in s:
        return _MOCK_SLACK_MESSAGES
    if "json_get_str" in s and "link" in s:
        return _MOCK_GITHUB_LINK
    if "vercel" in s or "deployment" in s:
        return _MOCK_DEPLOYMENTS
    if "codeowner" in s or "collaborator" in s or "oncall" in s:
        return _MOCK_OWNERSHIP
    return []


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class CoralQueryError(Exception):
    pass


class CoralRuntimeClient:
    """Executes SQL via the Coral CLI subprocess or returns mock data for dev."""

    def __init__(self, coral_config_dir: str | None = None) -> None:
        self._coral_config_dir = coral_config_dir

    def query(self, sql: str) -> list[dict]:
        if settings.coral_mode == CoralMode.mock:
            logger.debug("coral[mock] sql=%.120s", sql)
            return _mock_query(sql)

        logger.info("coral[cli] sql=%.120s", sql)
        env = None
        if self._coral_config_dir:
            env = os.environ.copy()
            env["CORAL_CONFIG_DIR"] = self._coral_config_dir

        try:
            result = subprocess.run(
                [settings.coral_binary, "sql", "--format", "json", sql],
                capture_output=True,
                text=True,
                timeout=settings.coral_sql_timeout,
                env=env,
            )
        except FileNotFoundError as exc:
            raise CoralQueryError(
                f"Coral binary '{settings.coral_binary}' not found. "
                "Set CORAL_MODE=mock or install Coral: brew install withcoral/tap/coral"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise CoralQueryError(
                f"Coral query timed out after {settings.coral_sql_timeout}s"
            ) from exc

        if result.returncode != 0:
            raise CoralQueryError(f"Coral error: {result.stderr.strip()}")

        try:
            data = json.loads(result.stdout)
            return data if isinstance(data, list) else data.get("rows", [data])
        except json.JSONDecodeError as exc:
            raise CoralQueryError(
                f"Could not parse Coral output: {result.stdout[:200]}"
            ) from exc
