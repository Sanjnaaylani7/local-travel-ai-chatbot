"""Lightweight access control for privileged endpoints.

Public chat/session/health endpoints are unauthenticated (they power a public
website widget). Administrative endpoints (e.g. feedback export) are protected
with a shared secret supplied via the ``X-Admin-Api-Key`` header and configured
through the ``ADMIN_API_KEY`` environment variable.
"""
from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from src.core.config import settings


def require_admin(x_admin_api_key: str = Header(default="", alias="X-Admin-Api-Key")) -> None:
    """FastAPI dependency enforcing the admin API key."""
    configured = settings.admin_api_key
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin endpoints are disabled (ADMIN_API_KEY not configured).",
        )
    if not x_admin_api_key or not secrets.compare_digest(x_admin_api_key, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key.",
        )
