from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.models import Organization, User
from app.db.session import get_db
from app.schemas.org_context import OrgContext
from app.services.org_integration_service import AuthService, OrgIntegrationService

_bearer = HTTPBearer(auto_error=False)


@dataclass
class SessionPrincipal:
    user: User
    organization: Organization
    org_context: OrgContext


def get_optional_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> SessionPrincipal | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        return None

    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    if not user_id or not org_id:
        return None

    auth = AuthService(db)
    user = auth.get_user(str(user_id))
    organization = auth.get_organization(str(org_id))
    if user is None or organization is None or user.organization_id != organization.id:
        return None

    org_ctx = OrgIntegrationService(db).build_org_context(organization)
    return SessionPrincipal(user=user, organization=organization, org_context=org_ctx)


def get_current_principal(
    principal: SessionPrincipal | None = Depends(get_optional_principal),
) -> SessionPrincipal:
    if principal is not None:
        return principal
    if not settings.auth_required:
        legacy = OrgIntegrationService.legacy_context_from_settings()
        if legacy is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sign in and configure your organization integrations.",
            )
        return SessionPrincipal(
            user=_LegacyUser(),
            organization=_LegacyOrganization(),
            org_context=legacy,
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )


class _LegacyUser:
    id = "legacy"
    email = "platform@reef.local"
    full_name = "Platform"
    organization_id = "legacy"


class _LegacyOrganization:
    id = "legacy"
    name = "Platform default"
    slug = "legacy"


def require_org_coral_ready(principal: SessionPrincipal = Depends(get_current_principal)) -> SessionPrincipal:
    if settings.coral_mode.value == "mock":
        return principal
    if principal.org_context.coral_ready or principal.org_context.organization_id == "legacy":
        return principal
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Configure GitHub, Sentry, Slack, and Vercel credentials in your organization profile first.",
    )
