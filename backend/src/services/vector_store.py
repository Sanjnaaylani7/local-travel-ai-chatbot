"""FAISS-backed vector store for semantic retrieval.

The index and its chunk metadata are produced by the data pipeline
(``data_pipeline/ingest/ingest_to_vector.py``) and shared with the backend via
a mounted volume / directory (``VECTOR_STORE_DIR``). The index uses inner
product over L2-normalised vectors, i.e. cosine similarity.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

INDEX_FILENAME = "index.faiss"
METADATA_FILENAME = "metadata.json"


class VectorStore:
    def __init__(self, store_dir: str | None = None):
        self.store_dir = Path(store_dir or settings.vector_store_dir)
        self._index = None
        self._metadata: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._loaded = False

    @property
    def index_path(self) -> Path:
        return self.store_dir / INDEX_FILENAME

    @property
    def metadata_path(self) -> Path:
        return self.store_dir / METADATA_FILENAME

    @property
    def is_ready(self) -> bool:
        return self._loaded and self._index is not None

    @property
    def size(self) -> int:
        return len(self._metadata)

    def load(self, force: bool = False) -> bool:
        """Load index + metadata from disk. Returns True on success."""
        with self._lock:
            if self._loaded and not force:
                return self._index is not None
            self._loaded = True
            if not self.index_path.exists() or not self.metadata_path.exists():
                logger.warning(
                    "Vector store not found in %s (index or metadata missing). "
                    "Retrieval will return no context until the pipeline is run.",
                    self.store_dir,
                )
                self._index = None
                self._metadata = []
                return False

            import faiss  # lazy import

            self._index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, "r", encoding="utf-8") as fh:
                self._metadata = json.load(fh)
            logger.info(
                "Loaded vector store: %d vectors from %s", self.size, self.store_dir
            )
            return True

    def search(self, query_embedding: np.ndarray, top_k: int | None = None) -> List[Dict[str, Any]]:
        """Return the most similar chunks with a cosine ``score`` field."""
        if not self._loaded:
            self.load()
        if self._index is None or self.size == 0:
            return []

        k = min(top_k or settings.top_k, self.size)
        query = np.asarray(query_embedding, dtype="float32")
        if query.ndim == 1:
            query = query.reshape(1, -1)

        scores, indices = self._index.search(query, k)
        results: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= self.size:
                continue
            chunk = dict(self._metadata[idx])
            chunk["score"] = float(score)
            results.append(chunk)
        return results


# Shared singleton used by the retrieval service.
vector_store = VectorStore()
