from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///shipguard.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_expiry_hours: int = 24
    # Allow explicit frontend origins
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173,"
        "http://localhost:5174,http://127.0.0.1:5174,"
        "http://localhost:5175,http://127.0.0.1:5175,"
        "http://localhost:5176,http://127.0.0.1:5176"
    )
    model_path: str = "app/ml/model.joblib"
    # Optional API key for NVIDIA / LLM integrations. Keep this out of version control.
    nvidia_api_key: str | None = None
    # Optional NVIDIA/OpenAI-compatible API URL and model
    nvidia_api_url: str | None = None
    nvidia_model: str | None = None
    # Google Gemini & OAuth configuration
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    # Rate Limiting configuration for AI Endpoints (Gemini & NVIDIA)
    ai_rate_limit_per_minute: int = 30
    ai_rate_limit_per_hour: int = 300
    ai_rate_limit_per_day: int = 1500
    gemini_daily_quota: int = 1000
    nvidia_daily_quota: int = 1000
    # Auth & API Rate Limiting
    auth_rate_limit_per_minute: int = 10
    auth_rate_limit_per_hour: int = 60
    sync_rate_limit_per_minute: int = 5
    # Password Policy
    min_password_length: int = 8

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

