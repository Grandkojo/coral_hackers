import dataclasses
import os
import re
import subprocess
from pathlib import Path

from app.core.config import CoralMode, settings
from app.core.logging import get_logger
from app.schemas.org_context import OrgContext

logger = get_logger(__name__)

_SOURCE_LINE = re.compile(r"(?:^|\s)(github|sentry|slack|vercel)(?:\s|$)")


def global_coral_config_dir() -> str:
    """Platform-wide Coral config (Docker volume), not a per-tenant subdirectory."""
    data_coral = Path("/data/coral")
    if data_coral.is_dir():
        return str(data_coral)
    env_dir = Path(os.environ.get("CORAL_CONFIG_DIR", "./data/coral"))
    parts = env_dir.parts
    if "orgs" in parts:
        idx = parts.index("orgs")
        return str(Path(*parts[:idx]))
    return str(env_dir)


def coral_has_any_source(config_dir: str) -> bool:
    """True when `coral source list` shows at least one registered integration."""
    if settings.coral_mode == CoralMode.mock:
        return True
    env = {**os.environ, "CORAL_CONFIG_DIR": config_dir}
    try:
        result = subprocess.run(
            ["coral", "source", "list"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.debug("coral source list failed for %s: %s", config_dir, exc)
        return False
    if result.returncode != 0:
        return False
    return _SOURCE_LINE.search(result.stdout) is not None

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


def _with_global_coral_fallback(org: OrgContext) -> OrgContext:
    """Use platform Coral dir when the per-org dir has no registered sources."""
    org_dir = org.coral_config_dir
    if coral_has_any_source(org_dir):
        return org
    global_dir = global_coral_config_dir()
    if global_dir != org_dir and coral_has_any_source(global_dir):
        logger.warning(
            "org %s: per-org coral at %s has no sources; using global %s",
            org.organization_slug,
            org_dir,
            global_dir,
        )
        return dataclasses.replace(org, coral_config_dir=global_dir)
    return org


def ensure_coral_ready_for_org(org: OrgContext) -> OrgContext:
    """Register tenant sources when possible; fall back to global Coral on disk."""
    if settings.coral_mode == CoralMode.mock:
        return org
    if not org.github_token:
        logger.warning(
            "org %s: cannot ensure coral — missing GitHub token in profile",
            org.organization_slug,
        )
        return _with_global_coral_fallback(org)
    configure_coral_for_org(org)
    return _with_global_coral_fallback(org)
