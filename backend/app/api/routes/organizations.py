from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import SessionPrincipal, get_current_principal
from app.db.session import get_db
from app.schemas.org import (
    OrganizationCredentialsResponse,
    OrganizationCredentialsUpdate,
    OrganizationProfileResponse,
)
from app.services.org_integration_service import OrgIntegrationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/me/profile", response_model=OrganizationProfileResponse)
def get_organization_profile(
    principal: SessionPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> OrganizationProfileResponse:
    service = OrgIntegrationService(db)
    integration = service.get_integration(principal.organization.id)
    return service.profile_response(principal.organization, integration)


@router.put("/me/credentials", response_model=OrganizationCredentialsResponse)
def update_organization_credentials(
    payload: OrganizationCredentialsUpdate,
    principal: SessionPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> OrganizationCredentialsResponse:
    service = OrgIntegrationService(db)
    try:
        profile = service.update_credentials(principal.organization, payload)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
    return OrganizationCredentialsResponse(
        organization_id=principal.organization.id,
        message="Integration credentials saved. Coral sources updated for your organization.",
        coral_ready=profile.coral_ready,
        profile=profile,
    )
