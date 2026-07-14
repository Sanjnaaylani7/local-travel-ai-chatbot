"""Session lifecycle endpoints (persisted in the database)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db import repository
from src.schemas.chat_schema import SessionResponse

router = APIRouter()


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(db: Session = Depends(get_db)) -> SessionResponse:
    session_id = str(uuid.uuid4())
    repository.create_session(db, session_id)
    return SessionResponse(session_id=session_id)


@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)) -> dict:
    deleted = repository.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return {"message": "Session deleted successfully."}
