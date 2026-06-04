"""Tests for the content diversity filter — prevents repeat recommendations."""

import os
import tempfile
import pytest
from pathlib import Path

from cinematic_mood_weaver.utils.diversity_filter import DiversityFilter


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
    yield
    if db_engine._engine:
        db_engine._engine.dispose()
    try:
        os.unlink(path)
    except PermissionError:
        pass
    cfg.settings.db_path = original


class TestDiversityFilter:
    def setup_method(self):
        self.filter = DiversityFilter(cooldown_days=7)

    def test_new_content_not_seen(self):
        assert self.filter.is_seen("movie_123") is False

    def test_mark_and_check_seen(self):
        self.filter.mark_seen("movie_123", "movie", "Test Movie")
        assert self.filter.is_seen("movie_123") is True

    def test_different_content_not_confused(self):
        self.filter.mark_seen("movie_123", "movie", "Test Movie")
        assert self.filter.is_seen("movie_456") is False

    def test_filter_new_removes_seen(self):
        items = [
            ("movie_1", "movie", "A"),
            ("movie_2", "movie", "B"),
            ("movie_3", "movie", "C"),
        ]
        self.filter.mark_seen("movie_2", "movie", "B")
        filtered = self.filter.filter_new(items)
        assert len(filtered) == 2
        assert ("movie_2", "movie", "B") not in filtered

    def test_mark_seen_does_not_duplicate(self):
        self.filter.mark_seen("id1", "movie", "Test")
        self.filter.mark_seen("id1", "movie", "Test")  # Should not raise
        assert self.filter.is_seen("id1") is True
