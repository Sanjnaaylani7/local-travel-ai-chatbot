"""Thin helper around a FAISS cosine-similarity index.

Vectors are expected to be L2-normalised so that inner product == cosine
similarity, matching the backend and data pipeline.
"""
from __future__ import annotations

from typing import List, Tuple

import faiss
import numpy as np


class IndexStore:
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)

    def add_embeddings(self, embeddings: np.ndarray) -> None:
        self.index.add(np.asarray(embeddings, dtype="float32"))

    def search(self, query_embedding: np.ndarray, k: int) -> Tuple[List[float], List[int]]:
        query = np.asarray(query_embedding, dtype="float32")
        if query.ndim == 1:
            query = query.reshape(1, -1)
        scores, indices = self.index.search(query, k)
        return scores[0].tolist(), indices[0].tolist()

    def save(self, path: str) -> None:
        faiss.write_index(self.index, path)

    def load(self, path: str) -> None:
        self.index = faiss.read_index(path)
