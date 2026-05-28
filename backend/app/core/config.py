from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class CoralMode(str, Enum):
    cli = "cli"
    mock = "mock"


class GitHubAccountType(str, Enum):
    user = "user"
    org = "org"


class Settings(BaseSettings):
    app_name: str = "Reef"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "sqlite:///./reef.db"

    # Coral integration
    coral_mode: CoralMode = CoralMode.mock
    coral_binary: str = "coral"
    coral_sql_timeout: int = 30
    max_investigation_iterations: int = 5

    # Decision thresholds
    confidence_threshold: float = 0.6
    severity_threshold: float = 0.7

    # Shared credentials (Reef remediation + Coral source setup via same .env)
    github_token: str = ""
    github_owner: str = ""
    github_repo: str = ""
    github_account_type: GitHubAccountType = GitHubAccountType.user
    sentry_org: str = ""
    sentry_token: str = ""
    slack_token: str = ""
    slack_incident_channel: str = "incidents"
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    vercel_token: str = ""

    # LLM planner (Phase 4B — optional)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Comma-separated browser origins allowed to call the API (Vercel frontend, local dev)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
