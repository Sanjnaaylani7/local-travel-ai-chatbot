"""JavaScript-aware fetcher for a single page using Playwright.

Useful for pages whose content is rendered client-side. Saves full HTML so the
standard cleaning step can process it. Requires ``playwright install chromium``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import BASE_URL, RAW_CONTENT_PATH, ensure_dirs  # noqa: E402


def fetch_page_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        html = page.content()
        browser.close()
    return html


def main() -> None:
    ensure_dirs()
    url = BASE_URL
    data = [{"url": url, "html": fetch_page_html(url)}]
    with open(RAW_CONTENT_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    print(f"Fetched {url} -> {RAW_CONTENT_PATH}")


if __name__ == "__main__":
    main()
