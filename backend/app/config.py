"""Application configuration loaded from environment variables.

All configuration is sourced from the environment (or a local ``.env`` file).
No secrets are hard-coded in the source tree.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database ---------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+psycopg2://dsa:dsa@localhost:5432/dsa_tracker",
        description="SQLAlchemy database URL.",
    )

    # CORS -------------------------------------------------------------------
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated list of allowed CORS origins.",
    )

    # Auth -------------------------------------------------------------------
    # NOTE: override JWT_SECRET_KEY in every non-local environment. The default
    # below is intentionally insecure and is rejected when APP_ENV=production.
    jwt_secret_key: str = Field(
        default="CHANGE_ME_INSECURE_DEV_SECRET",
        description="Secret used to sign JWT access tokens.",
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(
        default=60 * 24 * 7,  # 7 days — simple, long-lived token for this app.
        description="Access-token lifetime in minutes.",
    )

    # App --------------------------------------------------------------------
    app_env: str = Field(default="development", description="development|production")
    log_level: str = Field(default="INFO")

    app_name: str = "Study Plan Tracker API"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"

    @field_validator("app_env")
    @classmethod
    def _normalise_env(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def _guard_secret_in_production(self) -> "Settings":
        if self.app_env == "production" and (
            not self.jwt_secret_key
            or self.jwt_secret_key == "CHANGE_ME_INSECURE_DEV_SECRET"
        ):
            raise ValueError(
                "JWT_SECRET_KEY must be set to a strong value when APP_ENV=production."
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a clean list."""
        raw = (self.cors_origins or "").strip()
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
