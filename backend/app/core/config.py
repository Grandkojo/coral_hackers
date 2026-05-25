from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Coral Incident Agent"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "sqlite:///./coral_incident_agent.db"

    coral_runtime_base_url: str = "https://api.coral.example"
    github_token: str = ""
    vercel_token: str = ""
    sentry_token: str = ""
    slack_bot_token: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
