"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    APP_NAME: str = Field(default="SocialPilot AI")
    LOG_LEVEL: str = Field(default="INFO")
    LOG_JSON: bool = Field(default=True)

    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/socialpilot"
    )
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)
    DATABASE_ECHO: bool = Field(default=False)

    SECRET_KEY: str = Field(default="change-me-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TTL_MINUTES: int = Field(default=60)
    JWT_REFRESH_TTL_DAYS: int = Field(default=30)

    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TELEGRAM_BOT_USERNAME: str = Field(default="")
    TELEGRAM_INITDATA_MAX_AGE_SECONDS: int = Field(default=3600)
    TELEGRAM_NONCE_TTL_SECONDS: int = Field(default=86400)

    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash-lite")
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(default=1024)
    GEMINI_TIMEOUT_SECONDS: int = Field(default=30)
    GEMINI_DAILY_QUOTA_PER_COMPANY: int = Field(default=200)

    IMAGE_GENERATION_PROVIDER: str = Field(default="none")
    IMAGE_GENERATION_API_KEY: str = Field(default="")
    IMAGE_GENERATION_MODEL: str = Field(default="")
    IMAGE_GENERATION_DEFAULT_SIZE: str = Field(default="1024x1024")
    IMAGE_GENERATION_TIMEOUT_SECONDS: int = Field(default=60)
    IMAGE_GENERATION_QUOTA_PER_COMPANY_MONTH: int = Field(default=50)

    MEDIA_STORAGE_ROOT: str = Field(default="./data/media")
    MEDIA_MAX_UPLOAD_MB: int = Field(default=10)
    MEDIA_ALLOWED_EXTENSIONS: str = Field(default="jpg,jpeg,png,webp,gif,mp4")
    MEDIA_SERVE_PATH: str = Field(default="/media")

    CORS_ORIGINS: str = Field(default="https://telegram.org,https://web.telegram.org")
    RATE_LIMIT_PER_MINUTE: int = Field(default=100)

    PLATFORM_OWNER_TELEGRAM_ID: int | None = Field(default=None)
    COMPANY_REGISTRATION_MODE: str = Field(default="approval")
    INVITATION_TTL_HOURS: int = Field(default=72)
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=365)

    SENTRY_DSN: str = Field(default="")
    METRICS_ENABLED: bool = Field(default=False)

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}")
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        return v

    @field_validator("MEDIA_ALLOWED_EXTENSIONS")
    @classmethod
    def parse_media_extensions(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def media_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.MEDIA_ALLOWED_EXTENSIONS.split(",") if ext.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
