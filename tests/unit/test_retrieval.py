"""Unit tests for the retrieval service against the built FAISS index."""
import pytest

from src.services.retrieval import RetrievalService
from src.services.vector_store import vector_store


@pytest.fixture(scope="module")
def service():
    vector_store.load()
    if not vector_store.is_ready:
        pytest.skip("Vector store not built. Run data_pipeline/run_pipeline.py first.")
    return RetrievalService()


def test_retrieve_returns_relevant_chunks(service):
    results = service.retrieve_relevant_chunks("What documents are required for a visa?")
    assert isinstance(results, list)
    assert len(results) > 0
    combined = " ".join(c.get("content", "").lower() for c in results)
    assert "visa" in combined


def test_scores_are_sorted_descending(service):
    results = service.retrieve_relevant_chunks("flight booking and airline tickets", top_k=4)
    scores = [c["score"] for c in results]
    assert scores == sorted(scores, reverse=True)


def test_irrelevant_query_filtered_by_threshold(service):
    results = service.retrieve_relevant_chunks(
        "quantum chromodynamics lattice gauge theory", threshold=0.9
    )
    assert results == []


def test_empty_query_returns_empty(service):
    assert service.retrieve_relevant_chunks("   ") == []
