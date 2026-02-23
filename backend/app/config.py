import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    ENV: str = "development"
    DEBUG: bool = False  # 프로덕션 기본값

    # Supabase (필수)
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    # LLM (필수)
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str

    # App (필수 - 프로덕션에서는 환경변수로 설정해야 함)
    CORS_ORIGINS: str = "http://localhost:3000"

    # Admin (필수 - 프로덕션에서는 환경변수로 설정해야 함)
    ADMIN_API_KEY: str = "dev-admin-key"

    # Rate Limiting
    FREE_DAILY_LIMIT: int = 20

    # 개발 환경에서만 .env 파일 로드, 프로덕션에서는 환경변수만 사용
    model_config = SettingsConfigDict(
        env_file=".env" if os.getenv("ENV", "production") == "development" else None,
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
