"""Text embedding service backed by sentence-transformers.

The model is loaded lazily and cached process-wide so that multiple worker
threads share a single copy. Embeddings are L2-normalised so that a FAISS
inner-product index yields cosine similarity directly.
"""
from __future__ import annotations

import threading
from typing import List, Sequence

import numpy as np

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

_model = None
_model_lock = threading.Lock()


def get_model():
    """Return the shared SentenceTransformer instance (lazy, thread-safe)."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                # Imported lazily so unit tests can run without the heavy dependency.
                from sentence_transformers import SentenceTransformer

                logger.info("Loading embedding model: %s", settings.embedding_model)
                _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: Sequence[str]) -> np.ndarray:
    """Embed a batch of texts -> (n, dim) float32 array, L2-normalised."""
    model = get_model()
    vectors = model.encode(
        list(texts),
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype="float32")


def embed_query(text: str) -> np.ndarray:
    """Embed a single query -> (1, dim) float32 array."""
    return embed_texts([text])


def embedding_dimension() -> int:
    return int(get_model().get_sentence_embedding_dimension())


# Backwards-compatible helper (older code imported ``generate_embeddings``).
def generate_embeddings(text: str) -> List[float]:
    return embed_query(text)[0].tolist()
