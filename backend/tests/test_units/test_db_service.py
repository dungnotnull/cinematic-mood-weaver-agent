"""Tests for the database CRUD service — mood history, preferences, mashup log."""

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cinematic_mood_weaver.db.engine import Base, init_db
from cinematic_mood_weaver.db.service import (
    get_mood_history_since,
    get_recent_moods,
    get_user_preferences,
    log_mashup,
    rate_mashup,
    record_mood,
    save_user_preferences,
)
from cinematic_mood_weaver.types.models import (
    DiffuserSchedule,
    EmotionLabel,
    InterventionMode,
    LightScene,
    MashupSpec,
    UserPreferences,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Replace DB with a temp file for each test."""
    import cinematic_mood_weaver.db.engine as db_engine
    import cinematic_mood_weaver.config as cfg
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    path = f.name
    f.close()

    original = cfg.settings.db_path
    cfg.settings.db_path = path

    db_engine._engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    db_engine._SessionLocal = sessionmaker(bind=db_engine._engine, expire_on_commit=False)
    init_db()

    yield

    db_engine._engine.dispose()
    try:
        os.unlink(path)
    except PermissionError:
        pass
    cfg.settings.db_path = original


class TestMoodHistory:
    def test_record_and_retrieve(self):
        rid = record_mood(valence=0.5, arousal=0.3, label=EmotionLabel.HAPPY, confidence=0.9)
        assert rid > 0
        recent = get_recent_moods(limit=10)
        assert len(recent) == 1
        assert recent[0].label == EmotionLabel.HAPPY
        assert recent[0].valence == 0.5

    def test_multiple_entries(self):
        for i in range(5):
            record_mood(valence=0.1 * i, arousal=0.0, label=EmotionLabel.NEUTRAL, confidence=0.8)
        recent = get_recent_moods(limit=3)
        assert len(recent) == 3

    def test_get_history_since(self):
        record_mood(valence=0.5, arousal=0.3, label=EmotionLabel.HAPPY, confidence=0.9)
        entries = get_mood_history_since(hours=24)
        assert len(entries) >= 1


class TestUserPreferences:
    def test_save_and_load_defaults(self):
        prefs = get_user_preferences()
        assert prefs.session_duration_minutes == 90

    def test_save_and_load_custom(self):
        prefs = UserPreferences(
            preferred_genres=["sci-fi", "drama"],
            disliked_genres=["horror"],
            session_duration_minutes=60,
        )
        save_user_preferences(prefs)
        loaded = get_user_preferences()
        assert loaded.preferred_genres == ["sci-fi", "drama"]
        assert loaded.disliked_genres == ["horror"]
        assert loaded.session_duration_minutes == 60


class TestMashupLog:
    def test_log_and_rate(self):
        spec = MashupSpec(
            mood_target="test",
            intervention_mode=InterventionMode.MIRROR,
            narrative="Test mashup",
            film_query="test query",
            music_query="test music",
            light_scene=LightScene(scene_name="test", brightness=100, color_temperature=3500),
            diffuser_profile=DiffuserSchedule(oil_profile="lavender"),
        )
        mid = log_mashup(spec, "happy", 0.5, 0.3)
        assert mid > 0

        ok = rate_mashup(mid, 5)
        assert ok is True

        ok = rate_mashup(999, 3)
        assert ok is False

    def test_rate_invalid(self):
        with pytest.raises(ValueError):
            rate_mashup(1, 0)
