"""Tests for mood trajectory predictor."""

from datetime import datetime, timedelta

import pytest
from cinematic_mood_weaver.emotion.mood_trajectory import MoodTrajectoryPredictor
from cinematic_mood_weaver.types.models import EmotionHistoryEntry, EmotionLabel


def _make_entry(valence: float, arousal: float, minutes_ago: int = 0) -> EmotionHistoryEntry:
    return EmotionHistoryEntry(
        id=minutes_ago,
        timestamp=datetime.now() - timedelta(minutes=minutes_ago),
        valence=valence,
        arousal=arousal,
        label=EmotionLabel.NEUTRAL,
        confidence=0.8,
        source="test",
    )


class TestMoodTrajectory:
    def setup_method(self):
        self.predictor = MoodTrajectoryPredictor(window_hours=1, min_samples=3)

    def test_insufficient_data(self):
        result = self.predictor.predict([_make_entry(0.0, 0.0)])
        assert result.confidence == 0.0

    def test_improving_trend(self):
        entries = [
            _make_entry(-0.6, 0.0, minutes_ago=30),
            _make_entry(-0.3, 0.0, minutes_ago=20),
            _make_entry(0.0, 0.0, minutes_ago=10),
            _make_entry(0.2, 0.0, minutes_ago=0),
        ]
        result = self.predictor.predict(entries)
        assert result.trend_direction == "improving"

    def test_declining_trend(self):
        entries = [
            _make_entry(0.5, 0.0, minutes_ago=30),
            _make_entry(0.2, 0.0, minutes_ago=20),
            _make_entry(-0.1, 0.0, minutes_ago=10),
            _make_entry(-0.4, 0.0, minutes_ago=0),
        ]
        result = self.predictor.predict(entries)
        assert result.trend_direction == "declining"

    def test_stable_trend(self):
        entries = [_make_entry(0.0, 0.0, minutes_ago=i) for i in range(10, 0, -1)]
        result = self.predictor.predict(entries)
        assert result.trend_direction == "stable"

    def test_significant_shift_detected(self):
        entries = [
            _make_entry(0.0, 0.0, minutes_ago=10),
            _make_entry(0.1, 0.0, minutes_ago=5),
            _make_entry(-0.8, 0.0, minutes_ago=0),
        ]
        assert self.predictor.significant_shift_detected(entries) is True

    def test_no_shift_when_stable(self):
        entries = [_make_entry(0.0, 0.0, minutes_ago=i) for i in range(10, 0, -1)]
        assert self.predictor.significant_shift_detected(entries) is False
