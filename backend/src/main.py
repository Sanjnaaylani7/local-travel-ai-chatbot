"""FastAPI application entrypoint for the Local Travel AI Chatbot backend."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.chat import router as chat_router
from src.api.feedback import router as feedback_router
from src.api.health import router as health_router
from src.api.session import router as session_router
from src.core.config import settings
from src.core.logging_config import configure_logging, get_logger
from src.core.middleware import RateLimitMiddleware, RequestIDMiddleware

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from src.db.database import init_db
    from src.services.vector_store import vector_store

    init_db()
    vector_store.load()
    logger.info("%s v%s started (env=%s)", settings.app_name, settings.app_version, settings.environment)
    yield
    # Shutdown
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description="Self-hosted retrieval-augmented AI chatbot for travel support.",
    version=settings.app_version,
    lifespan=lifespan,
)

# --- Middleware (order matters: last added runs first) ---
app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global error handling ---
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled error (request_id=%s): %s", request_id, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


# --- Routes ---
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(session_router, prefix="/api/session", tags=["Session"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(health_router, prefix="/api/health", tags=["Health"])


@app.get("/")
async def root():
    return {"message": f"Welcome to the {settings.app_name} API!", "status": "running"}


# --- Optional Prometheus metrics ---
if settings.enable_metrics:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
        logger.info("Prometheus metrics enabled at /metrics")
    except Exception as exc:  # noqa: BLE001
        logger.info("Prometheus instrumentator not available (%s); /metrics disabled", exc)
