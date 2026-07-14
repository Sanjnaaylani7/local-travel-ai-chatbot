"""User feedback capture and admin export."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.security import require_admin
from src.db.database import get_db
from src.db import repository
from src.schemas.chat_schema import FeedbackRequest, FeedbackResponse

router = APIRouter()


@router.post("/", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)) -> FeedbackResponse:
    fb = repository.add_feedback(
        db,
        session_id=payload.session_id,
        user_message=payload.user_message,
        bot_response=payload.bot_response,
        rating=payload.rating,
        comments=payload.comments,
    )
    return FeedbackResponse(id=fb.id)


@router.get("/", dependencies=[Depends(require_admin)])
def list_feedback(db: Session = Depends(get_db)) -> dict:
    rows = repository.list_feedback(db)
    return {
        "count": len(rows),
        "items": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "rating": r.rating,
                "comments": r.comments,
                "user_message": r.user_message,
                "bot_response": r.bot_response,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }
