from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


CREATE_ARTICLES_TABLE = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    published_at TEXT,
    summary TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.execute(CREATE_ARTICLES_TABLE)
    connection.commit()
    return connection


def insert_article(
    connection: sqlite3.Connection,
    article: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO articles (
            source_id,
            source_name,
            title,
            url,
            published_at,
            summary
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            article["source_id"],
            article["source_name"],
            article["title"],
            article["url"],
            article["published_at"],
            article["summary"],
        ),
    )
    connection.commit()
