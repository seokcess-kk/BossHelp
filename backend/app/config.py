from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    ENV: str = "development"
    DEBUG: bool = True

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    # LLM
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str

    # App
    CORS_ORIGINS: str = "http://localhost:3000"

    # Admin
    ADMIN_API_KEY: str = "dev-admin-key"

    # Rate Limiting
    FREE_DAILY_LIMIT: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
