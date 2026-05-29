from dataclasses import dataclass

from app.core.config import GitHubAccountType


@dataclass(frozen=True)
class OrgContext:
    """Resolved tenant credentials for Coral queries and planner defaults."""

    organization_id: str
    organization_name: str
    organization_slug: str
    coral_config_dir: str
    github_token: str = ""
    github_owner: str = ""
    github_repo: str = ""
    github_account_type: GitHubAccountType = GitHubAccountType.org
    sentry_org: str = ""
    sentry_token: str = ""
    slack_token: str = ""
    slack_incident_channel: str = "incidents"
    vercel_token: str = ""
    coral_ready: bool = False

    def apply_to_trigger_context(self, context: dict[str, str]) -> dict[str, str]:
        enriched = dict(context)
        if self.github_owner and not enriched.get("github_owner"):
            enriched["github_owner"] = self.github_owner
        if self.github_repo and not enriched.get("github_repo"):
            enriched["github_repo"] = self.github_repo
        enriched["organization_id"] = self.organization_id
        enriched["organization_slug"] = self.organization_slug
        return enriched
