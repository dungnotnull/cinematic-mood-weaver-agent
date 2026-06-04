"""Background task scheduler for periodic mood sampling, knowledge updates, and data cleanup."""

from __future__ import annotations

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from cinematic_mood_weaver.config import settings

logger = logging.getLogger(__name__)


class PipelineScheduler:
    """Manages periodic background tasks for the Cinematic Mood Weaver.

    Tasks:
    - Periodic mood sampling (every 5 minutes during active sessions)
    - Knowledge brain update (weekly on Monday at 06:00)
    - Data cleanup (daily at 03:00 — purge old mood history)
    """

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None

    def start(self) -> None:
        """Start the APScheduler with all registered jobs."""
        self._scheduler = AsyncIOScheduler()
        self._register_jobs()
        self._scheduler.start()
        logger.info("Pipeline scheduler started")

    def stop(self) -> None:
        """Gracefully shut down the scheduler."""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            logger.info("Pipeline scheduler stopped")

    def _register_jobs(self) -> None:
        """Register all periodic jobs."""
        assert self._scheduler is not None

        # Data cleanup: purge mood history older than 90 days
        self._scheduler.add_job(
            self._cleanup_old_data,
            trigger="cron",
            hour=3,
            minute=0,
            id="data_cleanup",
            replace_existing=True,
        )

    async def _cleanup_old_data(self) -> None:
        """Purge mood history and mashup logs older than retention period."""
        from datetime import datetime, timedelta

        from cinematic_mood_weaver.db.engine import get_session
        from cinematic_mood_weaver.db.models import MashupLog, MoodHistory

        cutoff = datetime.now() - timedelta(days=90)
        session_factory = get_session()
        with session_factory() as session:
            mood_deleted = (
                session.query(MoodHistory)
                .filter(MoodHistory.timestamp < cutoff)
                .delete()
            )
            mashup_deleted = (
                session.query(MashupLog)
                .filter(MashupLog.timestamp < cutoff)
                .delete()
            )
            session.commit()
            if mood_deleted or mashup_deleted:
                logger.info(
                    f"Data cleanup: removed {mood_deleted} mood entries, {mashup_deleted} mashup logs"
                )
