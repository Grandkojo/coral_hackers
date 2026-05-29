from pydantic import BaseModel, Field

from app.core.config import GitHubAccountType


class OrganizationProfileResponse(BaseModel):
    organization_id: str
    name: str
    slug: str
    has_github: bool
    has_sentry: bool
    has_slack: bool
    has_vercel: bool
    github_owner: str = ""
    github_repo: str = ""
    github_account_type: GitHubAccountType = GitHubAccountType.org
    sentry_org: str = ""
    slack_incident_channel: str = "incidents"
    coral_ready: bool = False
    # Last 4 chars only — never return full secrets to the client
    github_token_hint: str = ""
    sentry_token_hint: str = ""
    slack_token_hint: str = ""
    vercel_token_hint: str = ""


class OrganizationCredentialsUpdate(BaseModel):
    github_token: str | None = None
    github_owner: str | None = None
    github_repo: str | None = None
    github_account_type: GitHubAccountType | None = None
    sentry_org: str | None = None
    sentry_token: str | None = None
    slack_token: str | None = None
    slack_incident_channel: str | None = None
    vercel_token: str | None = None


class OrganizationCredentialsResponse(BaseModel):
    organization_id: str
    message: str
    coral_ready: bool
    profile: OrganizationProfileResponse
