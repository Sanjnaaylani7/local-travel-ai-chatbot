"""Data-access helpers for chat sessions, messages and feedback."""
from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import ChatMessage, ChatSession, Feedback


# --- Sessions ---------------------------------------------------------------

def create_session(db: Session, session_id: str, user_id: Optional[str] = None) -> ChatSession:
    db_session = ChatSession(session_id=session_id, user_id=user_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_session(db: Session, session_id: str) -> Optional[ChatSession]:
    return db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    ).scalar_one_or_none()


def get_or_create_session(db: Session, session_id: str) -> ChatSession:
    existing = get_session(db, session_id)
    if existing:
        return existing
    return create_session(db, session_id)


def delete_session(db: Session, session_id: str) -> bool:
    db_session = get_session(db, session_id)
    if not db_session:
        return False
    db.delete(db_session)
    db.commit()
    return True


# --- Messages ---------------------------------------------------------------

def add_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    sources: Optional[List[str]] = None,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        sources=json.dumps(sources) if sources else None,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_recent_messages(db: Session, session_id: str, limit: int = 8) -> List[ChatMessage]:
    rows = db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.desc())
        .limit(limit)
    ).scalars().all()
    return list(reversed(rows))


# --- Feedback ---------------------------------------------------------------

def add_feedback(
    db: Session,
    session_id: Optional[str],
    user_message: Optional[str],
    bot_response: Optional[str],
    rating: Optional[int],
    comments: Optional[str],
) -> Feedback:
    fb = Feedback(
        session_id=session_id,
        user_message=user_message,
        bot_response=bot_response,
        rating=rating,
        comments=comments,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


def list_feedback(db: Session, limit: int = 200) -> List[Feedback]:
    rows = db.execute(
        select(Feedback).order_by(Feedback.id.desc()).limit(limit)
    ).scalars().all()
    return list(rows)
