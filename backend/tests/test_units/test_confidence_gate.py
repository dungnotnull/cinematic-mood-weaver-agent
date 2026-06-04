"""Tests for confidence gating — determines when user confirmation is needed."""

import os
import tempfile

import pytest
from cinematic_mood_weaver.emotion.confidence_gate import ConfidenceGate
from cinematic_mood_weaver.types.models import EmotionLabel, EmotionState, ValenceArousal


@pytest.fixture(autouse=True)
def temp_db():
    import cinematic_mood_weaver.db.engine as db_engine
    import cinematic_mood_weaver.config as cfg
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    path = f.name
    f.close()
    original = cfg.settings.db_path
    cfg.settings.db_path = path
    db_engine._engine = None
    db_engine._SessionLocal = None
    from cinematic_mood_weaver.db.engine import init_db
    init_db()
    yield
    if db_engine._engine:
        db_engine._engine.dispose()
    try:
        os.unlink(path)
    except PermissionError:
        pass
    cfg.settings.db_path = original


class TestConfidenceGate:
    def setup_method(self):
        self.gate = ConfidenceGate(threshold=0.6)

    def test_high_confidence_no_confirmation(self):
        emotion = EmotionState(va=ValenceArousal(valence=0.0, arousal=0.0), label=EmotionLabel.NEUTRAL, confidence=0.9)
        verdict = self.gate.evaluate(emotion)
        assert verdict.needs_confirmation is False

    def test_low_confidence_triggers_confirmation(self):
        emotion = EmotionState(va=ValenceArousal(valence=0.0, arousal=0.0), label=EmotionLabel.NEUTRAL, confidence=0.3)
        verdict = self.gate.evaluate(emotion)
        assert verdict.needs_confirmation is True
        assert "low_confidence" in verdict.reason

    def test_cooldown_prevents_spam(self):
        emotion = EmotionState(va=ValenceArousal(valence=0.0, arousal=0.0), label=EmotionLabel.NEUTRAL, confidence=0.3)
        verdict1 = self.gate.evaluate(emotion)
        assert verdict1.needs_confirmation is True
        # Second call within cooldown should not re-prompt
        verdict2 = self.gate.evaluate(emotion)
        assert verdict2.needs_confirmation is False

    def test_reset_clears_cooldown(self):
        emotion = EmotionState(va=ValenceArousal(valence=0.0, arousal=0.0), label=EmotionLabel.NEUTRAL, confidence=0.3)
        self.gate.evaluate(emotion)
        self.gate.reset()
        verdict = self.gate.evaluate(emotion)
        assert verdict.needs_confirmation is True
