from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DMS Email Monitor"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    database_url: str = "postgresql+asyncpg://postgres:app@localhost:5432/email_dig"
    redis_url: str = "redis://localhost:6379/0"

    azure_openai_endpoint: str = "https://gaebtesting1.openai.azure.com"
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-5.4-mini-ravi"

    slr_white_minutes: int = 4
    slr_yellow_minutes: int = 8
    email_poll_interval_seconds: int = 30
    max_emails_per_poll: int = 50

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
