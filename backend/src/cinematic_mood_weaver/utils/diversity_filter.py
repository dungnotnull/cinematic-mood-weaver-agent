"""Content diversity filter — prevents repeat recommendations within a
configurable window (default 7 days). Tracks seen content IDs in SQLite.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text

from cinematic_mood_weaver.db.engine import get_session

logger = logging.getLogger(__name__)


class DiversityFilter:
    """Tracks recently recommended content to prevent repeats.

    Stores seen content IDs in a dedicated SQLite table with timestamps.
    Filters out any content that was recommended within the cooldown window.
    """

    def __init__(self, cooldown_days: int = 7):
        self.cooldown_days = cooldown_days
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create the seen_content table if it doesn't exist."""
        session_factory = get_session()
        with session_factory() as session:
            session.execute(text(
                "CREATE TABLE IF NOT EXISTS seen_content ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "content_id TEXT UNIQUE NOT NULL, "
                "content_type TEXT NOT NULL, "
                "title TEXT, "
                "seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            ))
            session.commit()

    def is_seen(self, content_id: str) -> bool:
        """Check if a specific content item was recently recommended."""
        cutoff = datetime.now() - timedelta(days=self.cooldown_days)
        session_factory = get_session()
        with session_factory() as session:
            result = session.execute(
                text("SELECT 1 FROM seen_content WHERE content_id = :cid AND seen_at >= :cutoff"),
                {"cid": content_id, "cutoff": cutoff},
            ).fetchone()
            return result is not None

    def mark_seen(self, content_id: str, content_type: str, title: str = "") -> None:
        """Record that content was shown to the user."""
        session_factory = get_session()
        with session_factory() as session:
            try:
                session.execute(
                    text("INSERT OR IGNORE INTO seen_content (content_id, content_type, title) "
                         "VALUES (:cid, :ctype, :title)"),
                    {"cid": content_id, "ctype": content_type, "title": title},
                )
                session.commit()
            except Exception as e:
                logger.warning(f"Failed to mark content seen: {e}")

    def filter_new(self, items: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
        """Filter (content_id, content_type, title) tuples to only unseen items."""
        return [item for item in items if not self.is_seen(item[0])]

    def clear_expired(self) -> int:
        """Remove entries older than the cooldown window. Returns count removed."""
        cutoff = datetime.now() - timedelta(days=self.cooldown_days)
        session_factory = get_session()
        with session_factory() as session:
            result = session.execute(
                text("DELETE FROM seen_content WHERE seen_at < :cutoff"),
                {"cutoff": cutoff},
            )
            session.commit()
            count = result.rowcount
            if count:
                logger.info(f"Cleared {count} expired diversity filter entries")
            return count or 0
