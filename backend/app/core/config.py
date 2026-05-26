from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class CoralMode(str, Enum):
    cli = "cli"
    mock = "mock"


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

    # External services — write/remediation path only
    github_token: str = ""
    vercel_token: str = ""
    sentry_token: str = ""
    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    # LLM planner (Phase 4B — optional)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
