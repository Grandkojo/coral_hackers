from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import SessionPrincipal, get_current_principal
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import Organization, User
from app.db.session import get_db
from app.schemas.auth import (
    AuthOrganizationResponse,
    AuthSessionResponse,
    AuthUserResponse,
    LoginRequest,
    MeResponse,
    SignupRequest,
)
from app.services.org_integration_service import AuthService, OrgIntegrationService

router = APIRouter(prefix="/auth", tags=["auth"])


def _session_response(user: User, organization: Organization) -> AuthSessionResponse:
    token = create_access_token(
        user_id=user.id,
        organization_id=organization.id,
        email=user.email,
    )
    return AuthSessionResponse(
        access_token=token,
        user=AuthUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization_id=organization.id,
        ),
        organization=AuthOrganizationResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
        ),
    )


@router.post("/signup", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthSessionResponse:
    auth = AuthService(db)
    email = payload.email.lower().strip()
    if auth.get_user_by_email(email) is not None:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    slug = auth.create_unique_slug(payload.organization_name)
    organization = Organization(name=payload.organization_name.strip(), slug=slug)
    db.add(organization)
    db.flush()

    user = User(
        organization_id=organization.id,
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(organization)

    OrgIntegrationService(db).get_or_create_integration(organization.id)
    return _session_response(user, organization)


@router.post("/login", response_model=AuthSessionResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthSessionResponse:
    auth = AuthService(db)
    user = auth.get_user_by_email(payload.email.lower().strip())
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    organization = auth.get_organization(user.organization_id)
    if organization is None:
        raise HTTPException(status_code=500, detail="Organization not found.")

    return _session_response(user, organization)


@router.get("/me", response_model=MeResponse)
def me(principal: SessionPrincipal = Depends(get_current_principal)) -> MeResponse:
    return MeResponse(
        user=AuthUserResponse(
            id=principal.user.id,
            email=principal.user.email,
            full_name=principal.user.full_name,
            organization_id=principal.organization.id,
        ),
        organization=AuthOrganizationResponse(
            id=principal.organization.id,
            name=principal.organization.name,
            slug=principal.organization.slug,
        ),
    )
