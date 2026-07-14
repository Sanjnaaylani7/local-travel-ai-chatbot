"""Orchestrate the full data pipeline: crawl -> clean -> chunk -> ingest.

Examples
--------
    # Use the existing raw_content.json (skip network crawl) and rebuild the index
    python run_pipeline.py

    # Crawl the live site first, then rebuild
    python run_pipeline.py --crawl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from config import RAW_CONTENT_PATH  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the travel data pipeline.")
    parser.add_argument("--crawl", action="store_true", help="Crawl the live website first.")
    args = parser.parse_args()

    if args.crawl:
        from crawler.crawl import main as crawl_main

        crawl_main()
    elif not RAW_CONTENT_PATH.exists():
        raise SystemExit(
            f"{RAW_CONTENT_PATH} not found. Run with --crawl to fetch content first."
        )

    from extractor.clean import main as clean_main
    from chunker.chunk import main as chunk_main
    from ingest.ingest_to_vector import ingest_to_vector

    clean_main()
    chunk_main()
    ingest_to_vector()
    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
