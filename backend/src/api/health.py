"""Health and readiness endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from src.core.config import settings
from src.db.database import engine
from src.schemas.chat_schema import HealthResponse
from src.services.model_client import model_client
from src.services.vector_store import vector_store

router = APIRouter()


@router.get("/", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness check: always fast, does not depend on external services."""
    return HealthResponse(status="healthy", version=settings.app_version, checks={})


@router.get("/ready", response_model=HealthResponse)
def readiness(response: Response) -> HealthResponse:
    """Readiness check: verifies database, vector store and model server."""
    checks = {}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"

    if not vector_store.is_ready:
        vector_store.load()
    checks["vector_store"] = "ok" if vector_store.is_ready else "unavailable"
    checks["vector_store_size"] = vector_store.size

    checks["model_server"] = "ok" if model_client.health() else "unavailable"

    healthy = checks.get("database") == "ok"
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    overall = "ready" if healthy else "degraded"
    return HealthResponse(status=overall, version=settings.app_version, checks=checks)
