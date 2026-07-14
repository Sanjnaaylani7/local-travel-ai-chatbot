"""HTTP client for the local model server, plus RAG prompt construction."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=settings.model_max_retries,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset({"POST"}),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class ModelClient:
    def __init__(self, model_url: Optional[str] = None, timeout: Optional[float] = None):
        self.model_url = model_url or settings.model_url
        self.timeout = timeout or settings.model_timeout
        self._session = _build_session()

    def infer(self, prompt: str) -> Dict[str, Any]:
        try:
            resp = self._session.post(
                self.model_url, json={"input_text": prompt}, timeout=self.timeout
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as exc:
            logger.error("Model server request failed: %s", exc)
            return {"error": str(exc)}

    def health(self) -> bool:
        base = self.model_url.rsplit("/", 1)[0] + "/health"
        try:
            resp = self._session.get(base, timeout=5)
            return resp.status_code == 200
        except requests.exceptions.RequestException:
            return False


model_client = ModelClient()

_SYSTEM_INSTRUCTION = (
    "You are a helpful assistant for Rehman Travels, a travel agency. "
    "Answer the user's question using ONLY the information in the context below. "
    "If the context does not contain the answer, say you don't have that information "
    "and suggest contacting the travel experts. Be concise, accurate and friendly."
)


def build_prompt(
    query: str,
    chunks: Optional[List[Dict[str, Any]]] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    context_text = ""
    if chunks:
        parts = []
        for i, chunk in enumerate(chunks, start=1):
            content = (chunk.get("content") or "").strip()
            if content:
                parts.append(f"[{i}] {content}")
        context_text = "\n\n".join(parts)

    history_text = ""
    if history:
        turns = []
        for msg in history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            turns.append(f"{role}: {msg.get('content', '').strip()}")
        history_text = "\n".join(turns)

    sections = [_SYSTEM_INSTRUCTION]
    if context_text:
        sections.append(f"Context:\n{context_text}")
    if history_text:
        sections.append(f"Conversation so far:\n{history_text}")
    sections.append(f"Question:\n{query}\n\nAnswer:")
    return "\n\n".join(sections)


def generate_answer(
    query: str,
    chunks: Optional[List[Dict[str, Any]]] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Generate a grounded answer. Falls back to a safe message when the
    context is empty or the model server is unavailable."""
    if not chunks:
        return settings.fallback_message

    prompt = build_prompt(query, chunks, history)
    result = model_client.infer(prompt)

    if isinstance(result, dict):
        if "response" in result and result["response"]:
            return str(result["response"]).strip()
        if "error" in result:
            logger.warning("Falling back due to model error: %s", result["error"])
            return settings.fallback_message
    return settings.fallback_message


# Backwards-compatible alias used by older imports.
def generate_response(query: str, context=None, language: str = "auto") -> str:
    return generate_answer(query, context)
