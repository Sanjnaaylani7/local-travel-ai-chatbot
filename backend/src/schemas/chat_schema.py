"""Pydantic request/response schemas for the public API."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    language: str = "auto"
    user_id: Optional[str] = None


class Source(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    score: Optional[float] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[Source] = Field(default_factory=list)
    grounded: bool = True


class SessionResponse(BaseModel):
    session_id: str


class FeedbackRequest(BaseModel):
    session_id: Optional[str] = None
    user_message: Optional[str] = None
    bot_response: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comments: Optional[str] = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    id: int
    status: str = "recorded"


class HealthResponse(BaseModel):
    status: str
    version: str
    checks: dict
