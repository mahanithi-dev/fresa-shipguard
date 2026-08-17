from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, DotEnvSettingsSource


class Settings(BaseSettings):
    database_url: str = "sqlite:///./shipguard.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_expiry_hours: int = 24
    # Allow both localhost and 127.0.0.1 when serving the frontend from either host
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
    # Google Gemini API configuration
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    # Rate Limiting configuration for AI Endpoints (Gemini & NVIDIA)
    ai_rate_limit_per_minute: int = 15
    ai_rate_limit_per_hour: int = 200
    ai_rate_limit_per_day: int = 1000
    gemini_daily_quota: int = 500
    nvidia_daily_quota: int = 500

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

        # Fallback to .env.example if .env doesn't exist
        @classmethod
        def customise_sources(cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
            if not dotenv_settings:
                env_example = Path(__file__).parent.parent / ".env.example"
                if env_example.exists():
                    return (
                        init_settings,
                        env_settings,
                        DotEnvSettingsSource(BaseSettings, env_file=str(env_example), env_file_encoding="utf-8"),
                        file_secret_settings,
                    )
            return (init_settings, env_settings, dotenv_settings, file_secret_settings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
