from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Gloomberg API"
    debug: bool = True

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    financial_datasets_api_key: str = ""

    redis_url: str = "redis://localhost:6379"
    database_url: str = "postgresql+asyncpg://gloomberg:gloomberg@localhost:5432/gloomberg"

    cache_ttl_dashboard: int = 600  # 10 min - reduces Yahoo rate limit hits
    cache_ttl_ticker: int = 900
    cache_ttl_history: int = 3600
    cache_ttl_news: int = 1800

    jwt_secret: str = "gloomberg-dev-secret-change-in-production"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_pro: str = ""
    frontend_url: str = "http://localhost:3000"
    edgar_identity: str = "gloomberg@example.com"  # SEC requires identity for EDGAR requests

    class Config:
        env_file = ("../.env", ".env")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
