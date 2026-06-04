"""Adaptive sampling — dynamically adjusts SER polling frequency based on
mood volatility. Polls more frequently during instability, less during stability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from cinematic_mood_weaver.config import settings
from cinematic_mood_weaver.db.service import get_mood_history_since

logger = logging.getLogger(__name__)


@dataclass
class SamplingDecision:
    interval_seconds: int
    reason: str


class AdaptiveSampler:
    """Adjusts SER polling frequency based on recent mood volatility.

    - Stable mood (volatility < 0.2): poll every 300s (default)
    - Moderate volatility (0.2-0.5): poll every 120s
    - High volatility (> 0.5): poll every 60s
    - Significant shift detected: poll every 30s
    """

    def __init__(self, default_interval: int = 0):
        self.default_interval = default_interval or settings.ser_poll_interval_seconds
        self._current_interval = self.default_interval
        self._min_interval = 30
        self._max_interval = self.default_interval

    def decide(self) -> SamplingDecision:
        """Determine the next sampling interval based on recent emotion data."""
        recent = get_mood_history_since(hours=0.5)
        n = len(recent)

        if n < 3:
            return SamplingDecision(
                interval_seconds=self.default_interval,
                reason="insufficient_data",
            )

        valences = [e.valence for e in recent[-10:]]
        volatility = float(np.std(valences))
        range_val = max(valences) - min(valences)

        # Check for significant shifts (mood change > 0.5 in last 3 samples)
        if n >= 3:
            recent_vals = [e.valence for e in recent[-3:]]
            shift = abs(recent_vals[-1] - recent_vals[0])
            if shift > 0.5:
                interval = max(self._min_interval, 30)
                self._current_interval = interval
                return SamplingDecision(interval_seconds=interval, reason=f"significant_shift ({shift:.2f})")

        # Volatility-based intervals
        if volatility > 0.5:
            interval = 60
        elif volatility > 0.25:
            interval = 120
        else:
            interval = self.default_interval

        # If range is very wide, poll more frequently
        if range_val > 0.8:
            interval = min(interval, 60)

        self._current_interval = interval
        return SamplingDecision(
            interval_seconds=interval,
            reason=f"volatility={volatility:.2f}, range={range_val:.2f}",
        )

    @property
    def current_interval(self) -> int:
        return self._current_interval
