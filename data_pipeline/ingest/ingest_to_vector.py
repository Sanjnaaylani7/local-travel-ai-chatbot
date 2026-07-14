"""Embed chunks and build a FAISS cosine-similarity index for the backend.

Input:  ``output/chunks.json``
Output: ``<VECTOR_STORE_DIR>/index.faiss`` + ``metadata.json``

Uses L2-normalised embeddings with an inner-product index so that search
scores are cosine similarities in ``[-1, 1]``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import (  # noqa: E402
    CHUNKS_PATH,
    EMBEDDING_MODEL,
    INDEX_PATH,
    METADATA_PATH,
    ensure_dirs,
)


def ingest_to_vector() -> None:
    ensure_dirs()
    with open(CHUNKS_PATH, "r", encoding="utf-8") as fh:
        chunks = json.load(fh)

    if not chunks:
        raise SystemExit("No chunks found. Run the crawl/clean/chunk steps first.")

    print(f"Loaded {len(chunks)} chunks. Loading model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [c["content"] for c in chunks]
    embeddings = model.encode(
        texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True
    ).astype("float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))
    with open(METADATA_PATH, "w", encoding="utf-8") as fh:
        json.dump(chunks, fh, indent=2, ensure_ascii=False)

    print(f"Indexed {index.ntotal} vectors (dim={dimension}) -> {INDEX_PATH}")
    print(f"Wrote metadata -> {METADATA_PATH}")


if __name__ == "__main__":
    ingest_to_vector()
