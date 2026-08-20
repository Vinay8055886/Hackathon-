"""Central configuration, validated with Pydantic Settings.

Every environment variable is read through here — nothing in the codebase
reads ``os.environ`` directly.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AEGIS_",
        env_file=os.environ.get("AEGIS_ENV_FILE", str(PROJECT_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Runtime ──────────────────────────────────────────────────────────────
    env: str = "dev"
    log_level: str = "INFO"
    database_url: str = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'aegis.db'}"
    redis_url: str = "redis://localhost:6379/0"
    runner: str = "inproc"  # inproc | arq
    dry_run_default: bool = True
    max_concurrent_runs: int = 4

    # ── Auth ─────────────────────────────────────────────────────────────────
    jwt_secret: str = "change-me-in-production"
    jwt_alg: str = "HS256"
    jwt_expires_minutes: int = 480
    admin_username: str = "admin"
    admin_password: str = "admin"
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_scopes: str = "openid profile email"

    # ── Safety limits (enforced at the interaction boundary) ────────────────
    default_max_tokens_per_run: int = 200_000
    default_max_turns: int = 10
    rate_limit_per_minute: int = 60
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_cooldown_seconds: int = 60

    # ── LLM-as-judge (optional) ─────────────────────────────────────────────
    judge_api_base: str = "https://api.openai.com/v1"
    judge_api_key: str = ""
    judge_model: str = "gpt-4o-mini"

    # ── Embeddings (optional) ───────────────────────────────────────────────
    embedding_api_base: str = ""
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    vector_store: str = "numpy"  # numpy | pgvector

    # ── Reporting / CI ──────────────────────────────────────────────────────
    report_dir: Path = PROJECT_ROOT / "reports"
    ci_default_severity_threshold: str = "high"

    # ── Mock target ─────────────────────────────────────────────────────────
    mock_target_port: int = 8100

    # ── CORS (production) ───────────────────────────────────────────────────
    cors_allowed_origins: str = ""  # comma-separated list, e.g. "https://your-app.vercel.app"

    # ── Observability ───────────────────────────────────────────────────────
    enable_otel: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"

    @field_validator("runner")
    @classmethod
    def _validate_runner(cls, v: str) -> str:
        v = v.lower()
        if v not in {"inproc", "arq"}:
            raise ValueError("AEGIS_RUNNER must be 'inproc' or 'arq'")
        return v

    @field_validator("vector_store")
    @classmethod
    def _validate_vector_store(cls, v: str) -> str:
        v = v.lower()
        if v not in {"numpy", "pgvector"}:
            raise ValueError("AEGIS_VECTOR_STORE must be 'numpy' or 'pgvector'")
        return v

    @property
    def is_prod(self) -> bool:
        return self.env.lower() == "prod"

    @property
    def sqlalchemy_database_url(self) -> str:
        """Synchronous URL for Alembic (async drivers need the +aiosqlite/+asyncpg form)."""
        return self.database_url.replace("+aiosqlite", "").replace("+asyncpg", "")

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")


@lru_cache
def get_settings() -> Settings:
    return Settings()
