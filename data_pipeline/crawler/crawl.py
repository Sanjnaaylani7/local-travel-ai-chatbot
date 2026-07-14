"""Polite same-domain crawler that saves raw HTML for each visited page.

Output: ``output/raw_content.json`` -> ``[{"url": ..., "html": ...}]``
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urldefrag

import requests
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import BASE_URL, CRAWL_DELAY, MAX_PAGES, RAW_CONTENT_PATH, ensure_dirs  # noqa: E402

HEADERS = {"User-Agent": "RehmanTravelBot/1.0 (+https://rehmantravel.com)"}


class Crawler:
    def __init__(self, base_url: str, max_pages: int = 50, delay: float = 0.5):
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.delay = delay
        self.visited: set[str] = set()
        self.to_visit: list[str] = [self.base_url]
        self.pages: list[dict] = []

    def crawl(self) -> list[dict]:
        while self.to_visit and len(self.visited) < self.max_pages:
            url = urldefrag(self.to_visit.pop(0))[0]
            if url in self.visited:
                continue
            self.visited.add(url)
            html = self._fetch(url)
            if html is None:
                continue
            self.pages.append({"url": url, "html": html})
            self._enqueue_links(html, url)
            time.sleep(self.delay)

        print(f"Crawled {len(self.pages)} pages (visited {len(self.visited)}).")
        return self.pages

    def _fetch(self, url: str) -> str | None:
        try:
            resp = requests.get(url, timeout=15, headers=HEADERS)
            if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
                return resp.text
            print(f"Skip {url} (status={resp.status_code})")
        except requests.RequestException as exc:
            print(f"Error fetching {url}: {exc}")
        return None

    def _enqueue_links(self, html: str, base: str) -> None:
        soup = BeautifulSoup(html, "html.parser")
        for link in soup.find_all("a", href=True):
            full = urldefrag(urljoin(base, link["href"]))[0]
            if full.startswith(self.base_url) and full not in self.visited:
                self.to_visit.append(full)


def main() -> None:
    ensure_dirs()
    crawler = Crawler(BASE_URL, max_pages=MAX_PAGES, delay=CRAWL_DELAY)
    pages = crawler.crawl()
    with open(RAW_CONTENT_PATH, "w", encoding="utf-8") as fh:
        json.dump(pages, fh, indent=2, ensure_ascii=False)
    print(f"Saved raw content -> {RAW_CONTENT_PATH}")


if __name__ == "__main__":
    main()
