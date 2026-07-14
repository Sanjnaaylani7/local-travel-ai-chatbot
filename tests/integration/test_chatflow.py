"""Integration tests for the public API using FastAPI's TestClient."""
import pytest
from fastapi.testclient import TestClient

import src.api.chat as chat_module
from src.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    res = client.get("/api/health/")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_session_lifecycle(client):
    res = client.post("/api/session/")
    assert res.status_code == 201
    session_id = res.json()["session_id"]
    assert session_id

    delete = client.delete(f"/api/session/{session_id}")
    assert delete.status_code == 200


def test_delete_unknown_session_404(client):
    res = client.delete("/api/session/does-not-exist")
    assert res.status_code == 404


def test_chat_grounded_response(client, monkeypatch):
    # Deterministic model output so we don't need a running model server.
    monkeypatch.setattr(
        chat_module, "generate_answer", lambda q, chunks, history: "Here is your travel answer."
    )
    res = client.post("/api/chat/", json={"message": "Tell me about visa services", "language": "auto"})
    assert res.status_code == 200
    body = res.json()
    assert body["response"] == "Here is your travel answer."
    assert body["session_id"]
    assert body["grounded"] is True
    assert isinstance(body["sources"], list)


def test_chat_irrelevant_query_uses_fallback(client):
    res = client.post(
        "/api/chat/",
        json={"message": "zzxq lattice gauge chromodynamics", "language": "auto"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["grounded"] is False
    assert body["sources"] == []


def test_chat_validation_error(client):
    res = client.post("/api/chat/", json={"message": ""})
    assert res.status_code == 422


def test_feedback_recorded(client):
    res = client.post(
        "/api/feedback/",
        json={"rating": 5, "comments": "Very helpful!", "user_message": "hi", "bot_response": "hello"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "recorded"
    assert res.json()["id"] >= 1
