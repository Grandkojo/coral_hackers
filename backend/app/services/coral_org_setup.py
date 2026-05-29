import os
import subprocess
from pathlib import Path

from app.core.config import CoralMode, settings
from app.core.logging import get_logger
from app.schemas.org_context import OrgContext

logger = get_logger(__name__)

_VERCEL_MANIFEST = Path(__file__).resolve().parents[2] / "scripts" / "vercel-manifest.yaml"


def configure_coral_for_org(org: OrgContext) -> bool:
    """Register Coral sources for one tenant using their credentials."""
    if settings.coral_mode == CoralMode.mock:
        return True

    if not org.github_token:
        logger.warning("org %s: skip coral setup — no github token", org.organization_id)
        return False

    config_dir = Path(org.coral_config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update(
        {
            "CORAL_CONFIG_DIR": str(config_dir),
            "GITHUB_TOKEN": org.github_token,
            "GITHUB_OWNER": org.github_owner,
            "GITHUB_REPO": org.github_repo,
            "GITHUB_ACCOUNT_TYPE": org.github_account_type.value,
            "SENTRY_ORG": org.sentry_org,
            "SENTRY_TOKEN": org.sentry_token,
            "SLACK_TOKEN": org.slack_token,
            "SLACK_INCIDENT_CHANNEL": org.slack_incident_channel,
            "VERCEL_TOKEN": org.vercel_token,
            "CORAL_SETUP_SMOKE": "false",
        }
    )

    script = Path(__file__).resolve().parents[2] / "scripts" / "setup_coral_sources.sh"
    if not script.is_file():
        logger.error("coral setup script missing: %s", script)
        return False

    try:
        result = subprocess.run(
            ["bash", str(script)],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(script.parent.parent),
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.warning("org %s coral setup failed: %s", org.organization_id, exc)
        return False

    if result.returncode != 0:
        logger.warning(
            "org %s coral setup exit %s: %s",
            org.organization_id,
            result.returncode,
            result.stderr.strip()[:500],
        )
        return False

    logger.info("org %s coral sources configured at %s", org.organization_id, config_dir)
    return True
