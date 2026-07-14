"""Split cleaned documents into overlapping word-based chunks for embedding.

Input:  ``output/cleaned_data.json``
Output: ``output/chunks.json``
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import (  # noqa: E402
    CHUNKS_PATH,
    CHUNK_OVERLAP_WORDS,
    CHUNK_SIZE_WORDS,
    CLEANED_DATA_PATH,
    ensure_dirs,
)


def chunk_words(content: str, size: int, overlap: int) -> List[str]:
    words = content.split()
    if not words:
        return []
    step = max(1, size - overlap)
    chunks = []
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + size]).strip()
        if chunk:
            chunks.append(chunk)
        if start + size >= len(words):
            break
    return chunks


def main() -> None:
    ensure_dirs()
    with open(CLEANED_DATA_PATH, "r", encoding="utf-8") as fh:
        docs = json.load(fh)

    all_chunks: List[Dict[str, str]] = []
    for doc in docs:
        pieces = chunk_words(doc["content"], CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS)
        for i, piece in enumerate(pieces, start=1):
            all_chunks.append(
                {
                    "chunk_id": f"{doc.get('url', 'doc')}#${i}",
                    "content": piece,
                    "source_url": doc.get("url"),
                    "title": doc.get("title", "No Title"),
                    "category": "travel",
                }
            )

    with open(CHUNKS_PATH, "w", encoding="utf-8") as fh:
        json.dump(all_chunks, fh, indent=2, ensure_ascii=False)
    print(f"Chunking completed! {len(all_chunks)} chunks -> {CHUNKS_PATH}")


if __name__ == "__main__":
    main()
