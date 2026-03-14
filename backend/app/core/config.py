"""Configuration from environment."""
import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings. Override via env or .env file."""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://gloomberg:gloomberg@localhost:5432/gloomberg"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI-compatible LLM (e.g. OpenAI, LiteLLM)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"  # or LiteLLM URL
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Optional: Alpha Vantage (free tier)
    ALPHA_VANTAGE_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
