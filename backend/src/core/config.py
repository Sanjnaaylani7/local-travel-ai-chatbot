"""Application configuration.

Settings are loaded from environment variables (and an optional .env file)
so the same image can run in dev, staging and production without code changes.

We use a plain Pydantic v2 model plus python-dotenv instead of
``pydantic-settings`` to keep the dependency surface small.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env once, if present. Search upwards from this file to the repo root.
_here = Path(__file__).resolve()
for _candidate in [_here.parents[2], _here.parents[3], Path.cwd()]:
    _env_file = _candidate / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
        break

# Repository root (…/local-travel-ai-chatbot)
PROJECT_ROOT = _here.parents[3]


def _get(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value is not None and value != "" else default


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _get_list(name: str, default: List[str]) -> List[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings(BaseModel):
    """Typed application settings."""

    # --- Application ---
    app_name: str = Field(default_factory=lambda: _get("APP_NAME", "Local Travel AI Chatbot"))
    app_version: str = Field(default_factory=lambda: _get("APP_VERSION", "1.0.0"))
    environment: str = Field(default_factory=lambda: _get("ENV", "development"))
    log_level: str = Field(default_factory=lambda: _get("LOG_LEVEL", "INFO"))

    # --- Server ---
    host: str = Field(default_factory=lambda: _get("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: _get_int("PORT", 8000))

    # --- CORS ---
    cors_origins: List[str] = Field(default_factory=lambda: _get_list("CORS_ORIGINS", ["*"]))

    # --- Database ---
    database_url: str = Field(
        default_factory=lambda: _get("DATABASE_URL", f"sqlite:///{(PROJECT_ROOT / 'data' / 'app.db').as_posix()}")
    )

    # --- Model server ---
    model_url: str = Field(default_factory=lambda: _get("MODEL_URL", "http://localhost:8001/infer"))
    model_timeout: float = Field(default_factory=lambda: _get_float("MODEL_TIMEOUT", 60.0))
    model_max_retries: int = Field(default_factory=lambda: _get_int("MODEL_MAX_RETRIES", 2))

    # --- Embeddings / retrieval ---
    embedding_model: str = Field(
        default_factory=lambda: _get(
            "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    )
    vector_store_dir: str = Field(
        default_factory=lambda: _get(
            "VECTOR_STORE_DIR",
            (PROJECT_ROOT / "data_pipeline" / "output" / "vector_store").as_posix(),
        )
    )
    top_k: int = Field(default_factory=lambda: _get_int("TOP_K", 4))
    # Minimum cosine similarity for a chunk to be considered relevant.
    similarity_threshold: float = Field(
        default_factory=lambda: _get_float("SIMILARITY_THRESHOLD", 0.30)
    )

    # --- Conversation ---
    max_history_turns: int = Field(default_factory=lambda: _get_int("MAX_HISTORY_TURNS", 4))

    # --- Security / ops ---
    admin_api_key: str = Field(default_factory=lambda: _get("ADMIN_API_KEY", ""))
    rate_limit_per_minute: int = Field(default_factory=lambda: _get_int("RATE_LIMIT_PER_MINUTE", 60))
    enable_metrics: bool = Field(
        default_factory=lambda: _get("ENABLE_METRICS", "true").lower() in {"1", "true", "yes"}
    )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def fallback_message(self) -> str:
        return (
            "I'm sorry, I don't have verified information about that yet. "
            "I can help with visas, flights, tour packages, hotels, Umrah/Hajj and travel insurance. "
            "For anything else please contact our travel experts at info@rehmantravel.com."
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
