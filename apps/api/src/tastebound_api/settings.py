from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]
DEMO_WORKSPACE_ID = "demo-workspace"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(API_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    session_secret: str = "dev-secret-change-me"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "info"
    version: str = "0.1.0"

    database_url: str = ""
    sqlite_path: str = "data/tastebound.db"
    test_database_url: str = ""

    qloo_api_key: str = ""
    qloo_base_url: str = "https://hackathon.api.qloo.com"
    qloo_rps: float = 4.0
    qloo_max_calls_per_run: int = 200
    qloo_monthly_call_limit: int = 10_000
    qloo_cache_ttl_hours: int = 168
    qloo_timeout_seconds: float = 20.0
    scoring_strategy: str = "P"

    llm_provider: str = "ollama_cloud"
    ollama_base_url: str = "https://ollama.com/v1"
    ollama_api_key: str = ""
    ollama_model: str = "gemma4:31b-cloud"
    gemini_api_key: str = ""
    gemini_model: str = ""
    openai_compat_base_url: str = ""
    openai_compat_api_key: str = ""
    openai_compat_model: str = ""
    llm_timeout_seconds: float = 90.0
    llm_temperature_tools: float = 0.2
    llm_temperature_writing: float = 0.7
    llm_max_steps_per_phase: int = 12
    llm_max_calls_per_run: int = 40
    llm_tool_calling: bool = False

    website_fetch_timeout_seconds: float = 12.0

    demo_mode_enabled: bool = True
    demo_run_id: str = ""
    public_runs_per_ip_per_day: int = 30
    max_signature_items: int = 15
    max_markets_per_run: int = 40
    max_shortlist: int = 6

    @field_validator("app_env")
    @classmethod
    def _valid_env(cls, value: str) -> str:
        allowed = {"development", "test", "production"}
        if value not in allowed:
            raise ValueError(f"APP_ENV must be one of {sorted(allowed)}")
        return value

    @field_validator("scoring_strategy")
    @classmethod
    def _valid_strategy(cls, value: str) -> str:
        value = value.upper()
        if value not in {"P", "D", "H"}:
            raise ValueError("SCORING_STRATEGY must be P, D or H")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"

    @property
    def resolved_sqlite_path(self) -> Path:
        path = Path(self.sqlite_path)
        return path if path.is_absolute() else API_ROOT / path

    @property
    def database_dsn(self) -> str:
        if self.database_url:
            dsn = self.database_url
            if dsn.startswith("postgresql://"):
                return dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
            if dsn.startswith("postgres://"):
                return dsn.replace("postgres://", "postgresql+asyncpg://", 1)
            return dsn
        return f"sqlite+aiosqlite:///{self.resolved_sqlite_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
