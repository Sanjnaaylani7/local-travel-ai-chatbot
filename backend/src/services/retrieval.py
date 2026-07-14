"""Retrieval service: turn a user query into relevant knowledge chunks."""
from __future__ import annotations

from typing import Any, Dict, List

from src.core.config import settings
from src.core.logging_config import get_logger
from src.services.embeddings import embed_query
from src.services.vector_store import vector_store

logger = get_logger(__name__)


class RetrievalService:
    def __init__(self, store=vector_store):
        self.store = store

    def retrieve_relevant_chunks(
        self, query: str, top_k: int | None = None, threshold: float | None = None
    ) -> List[Dict[str, Any]]:
        """Return chunks whose cosine similarity to the query exceeds the threshold."""
        query = (query or "").strip()
        if not query:
            return []

        threshold = settings.similarity_threshold if threshold is None else threshold
        query_vec = embed_query(query)
        candidates = self.store.search(query_vec, top_k=top_k)
        relevant = [c for c in candidates if c.get("score", 0.0) >= threshold]
        logger.debug(
            "Retrieval: query=%r candidates=%d relevant=%d",
            query[:80], len(candidates), len(relevant),
        )
        return relevant


# Module-level singleton + helper used by the API layer.
retrieval_service = RetrievalService()


def retrieve_context(query: str) -> List[Dict[str, Any]]:
    return retrieval_service.retrieve_relevant_chunks(query)
