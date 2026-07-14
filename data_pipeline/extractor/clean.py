"""Clean raw crawled pages into normalised text documents.

Input:  ``output/raw_content.json``  (items with ``html`` or ``content``/``text``)
Output: ``output/cleaned_data.json`` (items with ``url``, ``title``, ``content``)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import CLEANED_DATA_PATH, RAW_CONTENT_PATH, ensure_dirs  # noqa: E402

_WHITESPACE_RE = re.compile(r"\s+")


def normalise_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", (text or "").replace("\n", " ")).strip()


def clean_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "button", "noscript", "form"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
    parts = []
    for node in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = node.get_text(" ", strip=True)
        if text:
            parts.append(text)
    content = normalise_text(" ".join(parts)) if parts else normalise_text(soup.get_text(" "))
    return {"title": title, "content": content}


def clean_item(item: dict) -> dict:
    if item.get("html"):
        cleaned = clean_html(item["html"])
    else:
        cleaned = {
            "title": item.get("title", "No Title"),
            "content": normalise_text(item.get("content") or item.get("text", "")),
        }
    return {"url": item.get("url"), "title": cleaned["title"], "content": cleaned["content"]}


def main() -> None:
    ensure_dirs()
    with open(RAW_CONTENT_PATH, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    cleaned = [clean_item(item) for item in raw]
    cleaned = [c for c in cleaned if c["content"]]

    with open(CLEANED_DATA_PATH, "w", encoding="utf-8") as fh:
        json.dump(cleaned, fh, indent=2, ensure_ascii=False)
    print(f"Cleaning completed! {len(cleaned)} documents -> {CLEANED_DATA_PATH}")


if __name__ == "__main__":
    main()
