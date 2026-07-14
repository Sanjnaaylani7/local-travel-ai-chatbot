"""Read URLs from a site's XML sitemap."""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup


class SitemapReader:
    def __init__(self, sitemap_url: str):
        self.sitemap_url = sitemap_url

    def fetch_sitemap(self) -> str:
        resp = requests.get(self.sitemap_url, timeout=15)
        resp.raise_for_status()
        return resp.text

    def parse_sitemap(self, content: str) -> list[str]:
        # Prefer the XML parser (lxml); fall back to the built-in parser.
        try:
            soup = BeautifulSoup(content, "xml")
        except Exception:
            soup = BeautifulSoup(content, "html.parser")
        return [loc.get_text(strip=True) for loc in soup.find_all("loc")]

    def get_urls(self) -> list[str]:
        return self.parse_sitemap(self.fetch_sitemap())


if __name__ == "__main__":
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "https://rehmantravel.com/sitemap.xml"
    for u in SitemapReader(url).get_urls():
        print(u)
