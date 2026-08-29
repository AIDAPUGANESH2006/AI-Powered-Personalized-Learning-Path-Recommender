from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PathWise AI"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = (
        "postgresql://pathwise:pathwise@localhost:5432/pathwise"
    )

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://pathwise-ai-frontend.onrender.com",
    ]

    # JWT
    secret_key: str = "change-me-in-production-use-a-long-random-string"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # AI — set at least one for LLM features (Phase 7+)
    gemini_api_key: str | None = None
    google_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


settings = Settings()
