"""Standalone embedding utility (kept consistent with the backend model).

The default model must match ``EMBEDDING_MODEL`` used by the backend and the
data pipeline so vectors are comparable.
"""
from __future__ import annotations

import os

from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


class Embedder:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts, normalize: bool = True):
        return self.model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=normalize
        )


if __name__ == "__main__":
    embedder = Embedder()
    samples = [
        "What documents are required for a Dubai visit visa?",
        "How long does visa processing take?",
    ]
    vectors = embedder.generate_embeddings(samples)
    print("shape:", vectors.shape)
