from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "news-scraper-backend"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = Field(
        default="postgresql+psycopg://news:news@db:5432/news_scraper",
        alias="DATABASE_URL",
    )
    scheduler_timezone: str = "America/New_York"
    daily_run_hour: int = 9
    daily_run_minute: int = 0
    run_on_startup: bool = False
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_summarization_model: str = Field(
        default="gpt-5.4-mini",
        alias="OPENAI_SUMMARIZATION_MODEL",
    )
    openai_social_model: str = Field(
        default="gpt-5.4-mini",
        alias="OPENAI_SOCIAL_MODEL",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
