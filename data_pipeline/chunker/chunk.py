"""Split cleaned documents into clean, topic-focused chunks for embedding.

Naive fixed-width word windows tend to start/end mid-sentence and mix unrelated
topics (e.g. "Umrah packages" bleeding into "car rentals"), which badly hurts
both retrieval precision and the answer quality of a small extractive model.

This chunker instead splits on *structural boundaries* — section headings and
numbered list items that are common on travel-agency sites — so that each chunk
is a single, self-contained topic. Long sections are further packed on sentence
boundaries so a chunk never starts or ends in the middle of a sentence.

Input:  ``output/cleaned_data.json``
Output: ``output/chunks.json``
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import (  # noqa: E402
    CHUNKS_PATH,
    CHUNK_SIZE_WORDS,
    CLEANED_DATA_PATH,
    ensure_dirs,
)

# Headings / list markers that begin a new self-contained section. The split is a
# look-ahead so the heading text stays attached to the content that follows it.
_SECTION_PATTERNS = [
    r"Explore These Welcoming[^.]*?Visit Visa Destinations",
    r"Explore Umrah Best Packages",
    r"Welcome to Rehman Travels",
    r"Services Offered by",
    r"\b[1-9]\d?\.\s+[A-Z][A-Za-z/&' ]{3,40}:",  # "1. Flight Booking:" …
    r"Popular Airlines on",
    r"Popular Hotels on",
    r"Get the Latest Deals",
    r"QUICK LINKS",
    r"OUR BRANCHES",
    r"CONTACT US",
]
_SPLIT_RE = re.compile("(?=" + "|".join(_SECTION_PATTERNS) + ")")

# Segments matching these are boilerplate/navigation and carry no answer value.
_JUNK_RE = re.compile(
    r"^(QUICK LINKS|Get the Latest Deals|Round Trip|USD Home|\+92|Subscribe)",
    re.IGNORECASE,
)

# Very common nav string that pollutes the first segment.
_NAV_PREFIX_RE = re.compile(
    r"^.*?(?=Explore These Welcoming|Welcome to Rehman Travels)", re.DOTALL
)

_SENT_RE = re.compile(r"(?<=[.!?])\s+")

# Repeated navigation/CTA fragments that add noise to answers.
_NOISE_RE = re.compile(
    r"\b(View Details?|Read More|Search|Book Now|Learn More|Request Call Back)\b",
    re.IGNORECASE,
)


def _clean_text(text: str) -> str:
    text = _NOISE_RE.sub("", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([.,])", r"\1", text)
    return text.strip()


def _pack_sentences(text: str, max_words: int) -> List[str]:
    """Pack sentences into chunks of at most ``max_words`` without splitting a
    sentence. Pipe-delimited lists (airlines/hotels) have no sentence breaks and
    are therefore kept intact as a single chunk."""
    sentences = _SENT_RE.split(text.strip())
    chunks: List[str] = []
    current: List[str] = []
    count = 0
    for sent in sentences:
        words = len(sent.split())
        if current and count + words > max_words:
            chunks.append(" ".join(current).strip())
            current, count = [], 0
        current.append(sent)
        count += words
    if current:
        chunks.append(" ".join(current).strip())
    return [c for c in chunks if c]


def _derive_title(text: str, fallback: str) -> str:
    """Best-effort human-readable topic label for a chunk."""
    m = re.match(r"\s*[1-9]\d?\.\s+([A-Z][A-Za-z/&' ]{2,40}):", text)
    if m:
        return m.group(1).strip()
    for label in (
        "Visit Visa Destinations",
        "Umrah Best Packages",
        "Popular Airlines",
        "Popular Hotels",
        "Welcome to Rehman Travels",
        "CONTACT US",
        "OUR BRANCHES",
    ):
        if text.lstrip().startswith(label) or label in text[:40]:
            return label
    return fallback


def chunk_document(content: str, max_words: int) -> List[Dict[str, str]]:
    content = _NAV_PREFIX_RE.sub("", content, count=1).strip() or content
    content = _clean_text(content)
    raw_segments = [s.strip() for s in _SPLIT_RE.split(content) if s.strip()]

    pieces: List[Dict[str, str]] = []
    for seg in raw_segments:
        if _JUNK_RE.match(seg) or len(seg.split()) < 4:
            continue
        title = _derive_title(seg, "Rehman Travels")
        for sub in _pack_sentences(seg, max_words):
            pieces.append({"content": sub, "chunk_title": title})
    return pieces


def main() -> None:
    ensure_dirs()
    with open(CLEANED_DATA_PATH, "r", encoding="utf-8") as fh:
        docs = json.load(fh)

    # Allow generous topic-sized chunks; sections stay whole where possible.
    max_words = max(CHUNK_SIZE_WORDS, 180)

    all_chunks: List[Dict[str, str]] = []
    for doc in docs:
        pieces = chunk_document(doc.get("content", ""), max_words)
        for i, piece in enumerate(pieces, start=1):
            all_chunks.append(
                {
                    "chunk_id": f"{doc.get('url', 'doc')}#${i}",
                    "content": piece["content"],
                    "source_url": doc.get("url"),
                    "title": piece["chunk_title"],
                    "category": "travel",
                }
            )

    with open(CHUNKS_PATH, "w", encoding="utf-8") as fh:
        json.dump(all_chunks, fh, indent=2, ensure_ascii=False)
    print(f"Chunking completed! {len(all_chunks)} chunks -> {CHUNKS_PATH}")


if __name__ == "__main__":
    main()
