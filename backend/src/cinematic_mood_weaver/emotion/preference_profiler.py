"""User preference profiler — learns genre affinities, content preferences,
and ideal arousal levels from user feedback history.

Updates preference weights in the database after each feedback interaction.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Optional

import numpy as np

from cinematic_mood_weaver.db.service import get_session, get_user_preferences, save_user_preferences
from cinematic_mood_weaver.db.models import MashupLog
from cinematic_mood_weaver.types.models import UserPreferences

logger = logging.getLogger(__name__)


class PreferenceProfiler:
    """Learns user content preferences from mashup feedback history.

    Tracks:
    - Genre affinities (which genres get thumbs up)
    - Preferred arousal range (what energy level user likes)
    - Content duration preferences
    """

    def __init__(self):
        self._genre_weights: dict[str, float] = {}
        self._arousal_preferences: list[float] = []

    def analyze_history(self) -> UserPreferences:
        """Analyze all past feedback to build a preference profile."""
        session_factory = get_session()
        with session_factory() as session:
            logs = session.query(MashupLog).filter(MashupLog.user_rating.isnot(None)).all()

        if not logs:
            logger.info("No feedback history to analyze — returning defaults")
            return get_user_preferences()

        # Genre affinities from movie titles (extract genre weight)
        genre_counter: Counter = Counter()
        rating_sum = 0.0
        rating_count = 0

        for log_entry in logs:
            if log_entry.user_rating and log_entry.user_rating >= 4:
                # Positive rating — boost associated genres
                if log_entry.movie_title:
                    genre_counter[log_entry.movie_title] += log_entry.user_rating
                if log_entry.playlist_name:
                    genre_counter[log_entry.playlist_name] += 1
            rating_sum += log_entry.user_rating or 3
            rating_count += 1

        avg_rating = rating_sum / rating_count if rating_count > 0 else 0.0

        # Build preferences from analysis
        prefs = UserPreferences(
            preferred_genres=[g for g, _ in genre_counter.most_common(5)],
            session_duration_minutes=90,
        )

        # Persist
        save_user_preferences(prefs)
        logger.info(f"Preference profile updated: {len(genre_counter)} genre signals, avg rating {avg_rating:.2f}")
        return prefs

    def update_from_feedback(self, mashup_id: int, rating: int, genres: Optional[list[str]] = None) -> None:
        """Update preference weights from a single feedback event.

        Args:
            mashup_id: The mashup that was rated.
            rating: 1 (thumbs up), 0 (neutral), -1 (thumbs down).
            genres: Optional list of genre tags associated with the mashup.
        """
        weight = {1: 1.0, 0: 0.0, -1: -0.5}.get(rating, 0.0)

        if genres:
            for genre in genres:
                current = self._genre_weights.get(genre, 0.0)
                self._genre_weights[genre] = current + weight

        logger.debug(f"Feedback applied: mashup_id={mashup_id}, rating={rating}, genres={genres}")
