"""Shared configuration and paths for the data pipeline.

Paths are resolved relative to this file so the scripts work regardless of the
current working directory. Everything is overridable via environment variables
so the pipeline can run in CI/containers.
"""
from __future__ import annotations

import os
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.getenv("PIPELINE_OUTPUT_DIR", str(PIPELINE_DIR / "output")))

RAW_CONTENT_PATH = OUTPUT_DIR / "raw_content.json"
CLEANED_DATA_PATH = OUTPUT_DIR / "cleaned_data.json"
CHUNKS_PATH = OUTPUT_DIR / "chunks.json"

# Must match the backend's VECTOR_STORE_DIR so it can load the index.
VECTOR_STORE_DIR = Path(os.getenv("VECTOR_STORE_DIR", str(OUTPUT_DIR / "vector_store")))
INDEX_PATH = VECTOR_STORE_DIR / "index.faiss"
METADATA_PATH = VECTOR_STORE_DIR / "metadata.json"

# Must match the backend's EMBEDDING_MODEL so query/document vectors align.
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Crawl settings.
BASE_URL = os.getenv("CRAWL_BASE_URL", "https://rehmantravel.com")
MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "50"))
CRAWL_DELAY = float(os.getenv("CRAWL_DELAY", "0.5"))

# Chunking settings (word-based with overlap).
CHUNK_SIZE_WORDS = int(os.getenv("CHUNK_SIZE_WORDS", "180"))
CHUNK_OVERLAP_WORDS = int(os.getenv("CHUNK_OVERLAP_WORDS", "40"))


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
