from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import feedparser
import requests

def fetch_feed(url: str, timeout: int = 20) -> dict[str, Any]:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "DailyFinancialAdviserBrief/1.0"})
    response.raise_for_status()
    parsed = feedparser.parse(response.content)
    return {"url": url, "status_code": response.status_code, "feed": parsed}

def normalize_entry(entry: Any, source_id: str, source_name: str) -> dict[str, Any]:
    published_at = None
    if getattr(entry, "published_parsed", None):
        published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
    return {
        "source_id": source_id,
        "source_name": source_name,
        "title": entry.get("title", "").strip(),
        "url": entry.get("link", "").strip(),
        "published_at": published_at,
        "summary": entry.get("summary", "").strip(),
    }

def collect_feed(url: str, source_id: str, source_name: str) -> list[dict[str, Any]]:
    result = fetch_feed(url)
    return [
        normalize_entry(entry, source_id, source_name)
        for entry in result["feed"].entries
        if entry.get("title") and entry.get("link")
    ]
