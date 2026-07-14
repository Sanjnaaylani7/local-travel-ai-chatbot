"""Database engine, session factory and declarative base.

Defaults to SQLite for local development but works unchanged with
PostgreSQL/MySQL in production by setting ``DATABASE_URL``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def _build_engine():
    url = settings.database_url
    connect_args = {}
    engine_kwargs = {"pool_pre_ping": True}

    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        # Ensure the parent directory for a file-based SQLite DB exists.
        if ":///" in url:
            db_path = url.split(":///", 1)[1]
            if db_path and db_path != ":memory:":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    else:
        # Sensible pool defaults for networked databases.
        engine_kwargs.update({"pool_size": 10, "max_overflow": 20, "pool_recycle": 1800})

    return create_engine(url, connect_args=connect_args, **engine_kwargs)


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create tables if they do not exist.

    For real production migrations use Alembic; this is a safe bootstrap.
    """
    # Import models so they register on Base.metadata before create_all.
    from src.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised (%s)", engine.url.render_as_string(hide_password=True))


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
