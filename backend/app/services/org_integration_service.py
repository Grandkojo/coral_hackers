import datetime
import os
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import GitHubAccountType, settings
from app.core.logging import get_logger
from app.db.models import Organization, OrganizationIntegration, User
from app.schemas.org import OrganizationCredentialsUpdate, OrganizationProfileResponse
from app.schemas.org_context import OrgContext
from app.services.coral_org_setup import configure_coral_for_org
from app.services.credential_crypto import decrypt_secret, encrypt_secret

logger = get_logger(__name__)


def token_hint(encrypted: str) -> str:
    """Masked preview for UI (last 4 characters only)."""
    if not encrypted:
        return ""
    try:
        plain = decrypt_secret(encrypted)
    except Exception:
        return "saved"
    if len(plain) <= 4:
        return "••••"
    return f"••••{plain[-4:]}"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:48] or "organization"


def resolve_coral_config_dir(organization_id: str, current_dir: str = "") -> str:
    """Pick a writable per-org Coral config directory."""
    candidates = []
    if current_dir:
        candidates.append(Path(current_dir))
    candidates.append(Path(settings.coral_orgs_base_dir) / organization_id)
    candidates.append(Path("./data/coral/orgs") / organization_id)

    seen: set[str] = set()
    for candidate in candidates:
        resolved = str(candidate.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return resolved
        except OSError as exc:
            logger.warning("cannot use coral dir %s: %s", resolved, exc)
    raise OSError(
        f"No writable Coral config directory for organization {organization_id}. "
        f"Set CORAL_ORGS_BASE_DIR in backend/.env to a writable path."
    )


class OrgIntegrationService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_integration(self, organization_id: str) -> OrganizationIntegration | None:
        return (
            self._db.query(OrganizationIntegration)
            .filter(OrganizationIntegration.organization_id == organization_id)
            .first()
        )

    def get_or_create_integration(self, organization_id: str) -> OrganizationIntegration:
        row = self.get_integration(organization_id)
        if row is not None:
            return row
        coral_dir = resolve_coral_config_dir(organization_id)
        row = OrganizationIntegration(
            organization_id=organization_id,
            coral_config_dir=coral_dir,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def build_org_context(self, organization: Organization) -> OrgContext:
        integration = self.get_or_create_integration(organization.id)
        account_type = GitHubAccountType.org
        if integration.github_account_type == GitHubAccountType.user.value:
            account_type = GitHubAccountType.user

        return OrgContext(
            organization_id=organization.id,
            organization_name=organization.name,
            organization_slug=organization.slug,
            coral_config_dir=integration.coral_config_dir
            or str(Path(settings.coral_orgs_base_dir) / organization.id),
            github_token=decrypt_secret(integration.github_token_enc),
            github_owner=integration.github_owner,
            github_repo=integration.github_repo,
            github_account_type=account_type,
            sentry_org=integration.sentry_org,
            sentry_token=decrypt_secret(integration.sentry_token_enc),
            slack_token=decrypt_secret(integration.slack_token_enc),
            slack_incident_channel=integration.slack_incident_channel or "incidents",
            vercel_token=decrypt_secret(integration.vercel_token_enc),
            coral_ready=integration.coral_ready == "true",
        )

    def profile_response(
        self, organization: Organization, integration: OrganizationIntegration | None
    ) -> OrganizationProfileResponse:
        if integration is None:
            return OrganizationProfileResponse(
                organization_id=organization.id,
                name=organization.name,
                slug=organization.slug,
            )
        return OrganizationProfileResponse(
            organization_id=organization.id,
            name=organization.name,
            slug=organization.slug,
            has_github=bool(integration.github_token_enc and integration.github_owner),
            has_sentry=bool(integration.sentry_token_enc and integration.sentry_org),
            has_slack=bool(integration.slack_token_enc),
            has_vercel=bool(integration.vercel_token_enc),
            github_owner=integration.github_owner,
            github_repo=integration.github_repo,
            github_account_type=(
                GitHubAccountType.org
                if integration.github_account_type != GitHubAccountType.user.value
                else GitHubAccountType.user
            ),
            sentry_org=integration.sentry_org,
            slack_incident_channel=integration.slack_incident_channel,
            coral_ready=integration.coral_ready == "true",
            github_token_hint=token_hint(integration.github_token_enc),
            sentry_token_hint=token_hint(integration.sentry_token_enc),
            slack_token_hint=token_hint(integration.slack_token_enc),
            vercel_token_hint=token_hint(integration.vercel_token_enc),
        )

    def update_credentials(
        self,
        organization: Organization,
        payload: OrganizationCredentialsUpdate,
    ) -> OrganizationProfileResponse:
        integration = self.get_or_create_integration(organization.id)
        integration.coral_config_dir = resolve_coral_config_dir(
            organization.id, integration.coral_config_dir
        )

        if payload.github_token is not None:
            integration.github_token_enc = encrypt_secret(payload.github_token.strip())
        if payload.github_owner is not None:
            integration.github_owner = payload.github_owner.strip()
        if payload.github_repo is not None:
            integration.github_repo = payload.github_repo.strip()
        if payload.github_account_type is not None:
            integration.github_account_type = payload.github_account_type.value
        if payload.sentry_org is not None:
            integration.sentry_org = payload.sentry_org.strip()
        if payload.sentry_token is not None:
            integration.sentry_token_enc = encrypt_secret(payload.sentry_token.strip())
        if payload.slack_token is not None:
            integration.slack_token_enc = encrypt_secret(payload.slack_token.strip())
        if payload.slack_incident_channel is not None:
            integration.slack_incident_channel = payload.slack_incident_channel.strip()
        if payload.vercel_token is not None:
            integration.vercel_token_enc = encrypt_secret(payload.vercel_token.strip())

        integration.updated_at = datetime.datetime.now(datetime.timezone.utc)
        self._db.commit()

        org_ctx = self.build_org_context(organization)
        try:
            ready = configure_coral_for_org(org_ctx)
        except Exception as exc:
            logger.exception("coral setup failed for org %s: %s", organization.id, exc)
            ready = False
        integration.coral_ready = "true" if ready else "false"
        self._db.commit()
        self._db.refresh(integration)

        return self.profile_response(organization, integration)

    @staticmethod
    def legacy_context_from_settings() -> OrgContext | None:
        if not settings.github_token and settings.coral_mode.value != "mock":
            return None
        return OrgContext(
            organization_id="legacy",
            organization_name="Platform default",
            organization_slug="legacy",
            coral_config_dir=os.environ.get("CORAL_CONFIG_DIR", "/data/coral"),
            github_token=settings.github_token,
            github_owner=settings.github_owner,
            github_repo=settings.github_repo,
            github_account_type=settings.github_account_type,
            sentry_org=settings.sentry_org,
            sentry_token=settings.sentry_token,
            slack_token=settings.slack_token or settings.slack_bot_token,
            slack_incident_channel=settings.slack_incident_channel,
            vercel_token=settings.vercel_token,
            coral_ready=True,
        )


class AuthService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self._db.query(User).filter(User.email == email.lower()).first()

    def get_user(self, user_id: str) -> User | None:
        return self._db.get(User, user_id)

    def get_organization(self, organization_id: str) -> Organization | None:
        return self._db.get(Organization, organization_id)

    def create_unique_slug(self, name: str) -> str:
        base = slugify(name)
        slug = base
        n = 1
        while (
            self._db.query(Organization).filter(Organization.slug == slug).first() is not None
        ):
            n += 1
            slug = f"{base}-{n}"
        return slug
