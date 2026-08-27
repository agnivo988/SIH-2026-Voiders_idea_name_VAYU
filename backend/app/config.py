from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Indian Airfare Price Index"
    database_url: str = "sqlite:///./airfare_index.db"
    demo_mode: bool = False
    enable_live_scraping: bool = False
    scrape_cron: str = "0 6 * * *"
    scrape_request_delay: float = 5.0
    live_request_timeout: float = 20.0
    live_max_retries: int = 2
    live_user_agent: str = "APIx-Research/0.1 (+approved-data-contact)"
    live_api_url: str | None = None
    admin_api_key: str = "change-me"
    base_period_days: int = 7
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
