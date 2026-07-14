"""Chat endpoint: retrieval-augmented generation over the travel knowledge base."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.logging_config import get_logger
from src.db.database import get_db
from src.db import repository
from src.schemas.chat_schema import ChatRequest, ChatResponse, Source
from src.services.model_client import generate_answer
from src.services.retrieval import retrieval_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    # Ensure we always have a session to attach the conversation to.
    session_id = request.session_id or str(uuid.uuid4())
    repository.get_or_create_session(db, session_id)

    # Retrieve grounding context.
    chunks = retrieval_service.retrieve_relevant_chunks(request.message)

    # Include recent conversation for continuity.
    history_rows = repository.get_recent_messages(db, session_id, limit=8)
    history = [{"role": m.role, "content": m.content} for m in history_rows]

    answer = generate_answer(request.message, chunks, history)
    grounded = bool(chunks)

    # Deduplicate sources by URL, preserving order.
    sources: list[Source] = []
    seen = set()
    for chunk in chunks:
        url = chunk.get("source_url") or chunk.get("url")
        if url and url in seen:
            continue
        if url:
            seen.add(url)
        sources.append(
            Source(title=chunk.get("title"), url=url, score=chunk.get("score"))
        )

    # Persist the turn.
    repository.add_message(db, session_id, "user", request.message)
    repository.add_message(
        db, session_id, "assistant", answer, sources=[s.url for s in sources if s.url]
    )

    return ChatResponse(
        response=answer, session_id=session_id, sources=sources, grounded=grounded
    )
