from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class CoralMode(str, Enum):
    cli = "cli"
    mock = "mock"


class GitHubAccountType(str, Enum):
    user = "user"
    org = "org"


class LlmProvider(str, Enum):
    gemini = "gemini"
    groq = "groq"
    # Legacy paid providers (optional; not used by default)
    openai = "openai"
    anthropic = "anthropic"


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
    max_github_queries_per_investigation: int = 2

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

    # Sentry webhook → background investigation + Slack notify
    webhook_organization_id: str = ""
    frontend_base_url: str = ""

    # LLM planner + judge (free tier: Gemini + Groq — leave keys empty for template/rules)
    planner_llm_provider: LlmProvider = LlmProvider.gemini
    judge_llm_provider: LlmProvider = LlmProvider.groq
    planner_model: str = ""
    judge_model: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # Legacy paid LLM keys (commented out in .env.example — not required for demo)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Comma-separated browser origins allowed to call the API (Vercel frontend, local dev)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Organization sessions (JWT) and encrypted tenant credentials
    jwt_secret: str = "change-me-in-production"
    credentials_encryption_key: str = ""
    auth_required: bool = False
    coral_orgs_base_dir: str = "./data/coral/orgs"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def resolved_planner_llm_provider(self) -> LlmProvider:
        return self.planner_llm_provider

    def resolved_judge_llm_provider(self) -> LlmProvider:
        return self.judge_llm_provider

    def resolved_planner_model(self) -> str:
        if self.planner_model.strip():
            return self.planner_model.strip()
        if self.planner_llm_provider == LlmProvider.gemini:
            return "gemini-2.5-flash"
        return "llama-3.3-70b-versatile"

    def resolved_judge_model(self) -> str:
        if self.judge_model.strip():
            return self.judge_model.strip()
        if self.judge_llm_provider == LlmProvider.groq:
            return "llama-3.3-70b-versatile"
        return "gemini-2.5-flash"


settings = Settings()
