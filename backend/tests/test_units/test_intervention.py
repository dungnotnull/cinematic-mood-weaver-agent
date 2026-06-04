"""Tests for the intervention selector — mirror/nudge/transform logic."""

import pytest
from datetime import datetime
from cinematic_mood_weaver.orchestration.intervention import InterventionSelector
from cinematic_mood_weaver.types.models import EmotionLabel, EmotionState, InterventionMode, ValenceArousal


class TestInterventionSelector:
    def setup_method(self):
        self.selector = InterventionSelector()

    def test_transform_when_target_set(self):
        emotion = EmotionState(va=ValenceArousal(valence=0.0, arousal=0.0), label=EmotionLabel.NEUTRAL, confidence=0.8)
        target = ValenceArousal(valence=0.5, arousal=0.5)
        mode = self.selector.select(emotion, target=target)
        assert mode == InterventionMode.TRANSFORM

    def test_mirror_default(self):
        emotion = EmotionState(va=ValenceArousal(valence=0.3, arousal=0.2), label=EmotionLabel.CALM, confidence=0.8)
        mode = self.selector.select(emotion)
        assert mode == InterventionMode.MIRROR

    def test_nudge_late_night(self):
        """After 23:00 should always nudge toward calm."""
        emotion = EmotionState(va=ValenceArousal(valence=0.5, arousal=0.5), label=EmotionLabel.HAPPY, confidence=0.8)

        # Monkey-patch datetime for testing
        import cinematic_mood_weaver.orchestration.intervention as mod
        original = mod.datetime

        class FakeDatetime:
            @staticmethod
            def now():
                return datetime(2026, 1, 1, 23, 30)

            @staticmethod
            def fromtimestamp(ts):
                return datetime.fromtimestamp(ts)

        mod.datetime = FakeDatetime  # type: ignore
        try:
            mode = self.selector.select(emotion)
            assert mode == InterventionMode.NUDGE
        finally:
            mod.datetime = original
