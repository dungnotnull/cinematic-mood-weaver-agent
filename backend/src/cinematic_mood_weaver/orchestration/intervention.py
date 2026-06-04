"""Intervention mode selector — determines mirror/nudge/transform based on
current emotion state, mood history, time of day, and user target mood.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from cinematic_mood_weaver.db.service import get_mood_history_since, get_user_preferences
from cinematic_mood_weaver.types.models import EmotionState, InterventionMode, ValenceArousal

logger = logging.getLogger(__name__)


class InterventionSelector:
    """Chooses how strongly to intervene based on emotional context.

    Decision logic:
    - If user specified a target mood → TRANSFORM
    - If mood is trending negative over the last hour → NUDGE
    - If mood is already positive/neutral → MIRROR
    - Late night (after 23:00) → NUDGE toward calm/sleep
    """

    def __init__(self) -> None:
        self._last_intervention: InterventionMode = InterventionMode.MIRROR

    def select(
        self,
        current: EmotionState,
        target: Optional[ValenceArousal] = None,
    ) -> InterventionMode:
        """Select intervention mode based on current state and context."""
        # If a target mood is explicitly set, always transform
        if target is not None:
            self._last_intervention = InterventionMode.TRANSFORM
            return InterventionMode.TRANSFORM

        # Check time of day — late night nudges toward calm
        hour = datetime.now().hour
        if hour >= 23 or hour < 5:
            self._last_intervention = InterventionMode.NUDGE
            return InterventionMode.NUDGE

        # Check recent history for negative trends
        recent: list = []
        try:
            recent = get_mood_history_since(hours=1)
        except Exception:
            logger.debug("No mood history available (DB not initialized yet)")

        if len(recent) >= 3:
            recent_valences = [e.valence for e in recent[-3:]]
            trend = recent_valences[-1] - recent_valences[0]
            if trend < -0.3 and current.va.valence < 0:
                self._last_intervention = InterventionMode.NUDGE
                return InterventionMode.NUDGE
            if current.va.valence < -0.5:
                self._last_intervention = InterventionMode.TRANSFORM
                return InterventionMode.TRANSFORM

        # Default: mirror the current mood
        self._last_intervention = InterventionMode.MIRROR
        return InterventionMode.MIRROR

    @property
    def last_intervention(self) -> InterventionMode:
        return self._last_intervention
