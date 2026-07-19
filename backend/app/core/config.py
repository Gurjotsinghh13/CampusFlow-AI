from dataclasses import Field
import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "CampusFlow AI"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/campusflow"

    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    LOGIN_RATE_LIMIT_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 300
    LOGIN_RATE_LIMIT_MAX_KEYS: int = 10_000

    ADMIN_EMAIL: str = "admin@campusflow.ai"
    ADMIN_PASSWORD_HASH: str = ""  # set via seed script

    from pydantic import Field

    CORS_ORIGINS: list[str] = Field(default_factory=list)

    SOLVER_MAX_TIME_SECONDS: int = 120
    SOLVER_NUM_WORKERS: int = 8

    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []
            if raw_value.startswith("["):
                parsed = json.loads(raw_value)
            else:
                parsed = [origin.strip() for origin in raw_value.split(",")]
            return [origin for origin in parsed if origin]
        if isinstance(value, list):
            return [origin.strip() for origin in value if isinstance(origin, str) and origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
