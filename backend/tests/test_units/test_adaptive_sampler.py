"""Tests for adaptive sampling — dynamic SER polling frequency."""

import os
import tempfile
from datetime import datetime, timedelta

import pytest
from cinematic_mood_weaver.emotion.adaptive_sampler import AdaptiveSampler


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


class TestAdaptiveSampler:
    def setup_method(self):
        self.sampler = AdaptiveSampler(default_interval=300)

    def test_default_interval(self):
        decision = self.sampler.decide()
        assert decision.interval_seconds == 300

    def test_interval_range(self):
        assert self.sampler.current_interval >= 30
        assert self.sampler.current_interval <= 300
