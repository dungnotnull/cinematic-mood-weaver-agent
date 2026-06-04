"""End-to-end integration tests for the full pipeline with mocked external APIs."""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from cinematic_mood_weaver.pipeline import MoodWeaverPipeline
from cinematic_mood_weaver.types.models import (
    EmotionLabel,
    EmotionState,
    InterventionMode,
    MashupSpec,
    PipelineConfig,
    ValenceArousal,
)


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


@pytest.mark.asyncio
class TestE2EPipeline:
    async def test_pipeline_initializes(self):
        pipeline = MoodWeaverPipeline()
        await pipeline.initialize()
        assert pipeline._initialized is True
        assert pipeline.ser_ensemble is not None
        assert pipeline.llm_chain is not None

    async def test_generate_mashup_from_emotion(self):
        pipeline = MoodWeaverPipeline()
        await pipeline.initialize()

        emotion = EmotionState(
            va=ValenceArousal(valence=-0.4, arousal=0.7),
            label=EmotionLabel.ANXIOUS,
            confidence=0.85,
        )
        result = await pipeline.generate_mashup(emotion)
        assert result.spec is not None
        assert result.spec.narrative != ""
        assert result.spec.film_query != ""
        assert result.spec.music_query != ""
        assert result.pipeline_ms > 0
        assert result.emotion_state.label == EmotionLabel.ANXIOUS

    async def test_mashup_contains_all_sections(self):
        pipeline = MoodWeaverPipeline()
        await pipeline.initialize()

        emotion = EmotionState(
            va=ValenceArousal(valence=0.5, arousal=0.6),
            label=EmotionLabel.HAPPY,
            confidence=0.9,
        )
        result = await pipeline.generate_mashup(emotion)
        assert result.spec.movie is not None
        assert len(result.spec.playlists) > 0
        assert result.spec.light_scene.scene_name != ""
        assert result.spec.diffuser_profile.oil_profile != ""

    async def test_pipeline_uses_template_fallback(self):
        """When no LLM API keys are configured, should use template fallback."""
        pipeline = MoodWeaverPipeline()
        await pipeline.initialize()

        emotion = EmotionState(
            va=ValenceArousal(valence=-0.8, arousal=-0.5),
            label=EmotionLabel.SAD,
            confidence=0.75,
        )
        result = await pipeline.generate_mashup(emotion)
        assert result.spec.intervention_mode == InterventionMode.MIRROR
        # Template should generate a valid narrative
        assert len(result.spec.narrative) > 10
        assert result.spec.movie is not None
