"""Mood trajectory predictor — detects trending emotional shifts using
time-series analysis on the mood history log.

Supports:
- Simple linear trend detection (slope over last N samples)
- Volatility detection (standard deviation of recent valence)
- Predicted mood direction for the next sampling window
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from cinematic_mood_weaver.db.service import get_mood_history_since, get_recent_moods
from cinematic_mood_weaver.types.models import EmotionHistoryEntry, ValenceArousal


@dataclass
class TrajectoryForecast:
    """Predicted mood trajectory over the next window."""

    predicted_va: ValenceArousal
    trend_direction: str  # "improving" | "declining" | "stable"
    trend_slope: float  # valence change per hour
    volatility: float  # std dev of valence over window
    confidence: float  # 0-1, higher when more data is available
    window_hours: int = 1


class MoodTrajectoryPredictor:
    """Predicts short-term mood trends from historical emotion data.

    Uses a simple linear regression on recent valence values to determine
    whether the user's mood is improving, declining, or stable.
    """

    def __init__(self, window_hours: int = 1, min_samples: int = 5):
        self.window_hours = window_hours
        self.min_samples = min_samples

    def predict(self, entries: Optional[list[EmotionHistoryEntry]] = None) -> TrajectoryForecast:
        """Predict mood trajectory from recent history.

        Args:
            entries: Optional pre-fetched history. If None, fetches automatically.

        Returns:
            TrajectoryForecast with predicted VA, trend, volatility, confidence.
        """
        if entries is None:
            entries = get_mood_history_since(hours=self.window_hours)

        n = len(entries)
        if n < self.min_samples:
            # Not enough data for meaningful prediction
            last = entries[-1] if entries else EmotionHistoryEntry(
                id=0, timestamp=datetime.now(), valence=0.0, arousal=0.0,
                label="neutral", confidence=0.0, source="default",
            )
            return TrajectoryForecast(
                predicted_va=ValenceArousal(valence=last.valence, arousal=last.arousal),
                trend_direction="stable",
                trend_slope=0.0,
                volatility=0.0,
                confidence=0.0,
                window_hours=self.window_hours,
            )

        # Extract valence and time (in hours from first entry) for regression
        t0 = entries[0].timestamp
        times = np.array([(e.timestamp - t0).total_seconds() / 3600.0 for e in entries])
        valences = np.array([e.valence for e in entries])
        arousals = np.array([e.arousal for e in entries])

        # Linear regression on valence
        slope, intercept = self._linear_regression(times, valences)

        # Predicted valence 1 hour ahead
        next_time = times[-1] + 1.0
        predicted_valence = slope * next_time + intercept
        predicted_valence = float(np.clip(predicted_valence, -1.0, 1.0))

        # Average arousal as prediction
        predicted_arousal = float(np.mean(arousals))

        # Trend direction
        if slope > 0.05:
            direction = "improving"
        elif slope < -0.05:
            direction = "declining"
        else:
            direction = "stable"

        # Volatility (standard deviation of recent valence)
        volatility = float(np.std(valences))

        # Confidence: higher when more samples exist and trend is clearer
        confidence = min(1.0, (n / 20) * (1.0 - abs(slope) / 2.0))
        confidence = max(0.1, min(1.0, confidence))

        return TrajectoryForecast(
            predicted_va=ValenceArousal(valence=round(predicted_valence, 4), arousal=round(predicted_arousal, 4)),
            trend_direction=direction,
            trend_slope=round(float(slope), 4),
            volatility=round(volatility, 4),
            confidence=round(confidence, 4),
            window_hours=self.window_hours,
        )

    def significant_shift_detected(self, entries: Optional[list[EmotionHistoryEntry]] = None) -> bool:
        """Detect if a significant mood shift just occurred.

        A shift is significant if the current valence differs from the
        running mean by more than 2 * volatility.
        """
        if entries is None:
            entries = get_mood_history_since(hours=1)

        if len(entries) < 3:
            return False

        current = entries[-1].valence
        mean_val = float(np.mean([e.valence for e in entries[:-1]]))
        std_val = float(np.std([e.valence for e in entries[:-1]])) or 0.1

        return abs(current - mean_val) > 2.0 * std_val

    @staticmethod
    def _linear_regression(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
        """Fit y = slope * x + intercept using least squares."""
        n = len(x)
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        if denominator == 0:
            return 0.0, float(y_mean)
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        return float(slope), float(intercept)
