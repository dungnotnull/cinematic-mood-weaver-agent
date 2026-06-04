"""Core pipeline — wires all modules together for the end-to-end mashup generation flow.

Voice → SER → Emotion State → Intervention Mode → LLM Mashup → Content APIs → Mashup Result
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, Optional

from cinematic_mood_weaver.clients.lighting_client import LightingClient
from cinematic_mood_weaver.clients.spotify_client import SpotifyClient
from cinematic_mood_weaver.clients.tmdb_client import TMDBClient
from cinematic_mood_weaver.db.service import get_user_preferences, log_mashup, record_mood
from cinematic_mood_weaver.emotion.emotion_mapper import EmotionMapper
from cinematic_mood_weaver.emotion.ser_engine import SEREnsemble
from cinematic_mood_weaver.orchestration.intervention import InterventionSelector
from cinematic_mood_weaver.orchestration.llm_backends import FallbackChain
from cinematic_mood_weaver.sensors.audio_capture import AudioCapture, AudioChunk
from cinematic_mood_weaver.types.models import EmotionState, MashupResult, MashupSpec, PipelineConfig, UserProfile

logger = logging.getLogger(__name__)


class MoodWeaverPipeline:
    """End-to-end pipeline orchestrating all modules.

    Usage:
        pipeline = MoodWeaverPipeline()
        await pipeline.initialize()
        result = await pipeline.process_audio_chunk(audio_chunk)
        # or
        await pipeline.run_continuous(on_mashup=my_callback)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self._initialized = False

        # Components (lazy-initialized)
        self.audio_capture: Optional[AudioCapture] = None
        self.ser_ensemble: Optional[SEREnsemble] = None
        self.emotion_mapper: Optional[EmotionMapper] = None
        self.intervention_selector: Optional[InterventionSelector] = None
        self.llm_chain: Optional[FallbackChain] = None
        self.spotify: Optional[SpotifyClient] = None
        self.tmdb: Optional[TMDBClient] = None
        self.lighting: Optional[LightingClient] = None

    async def initialize(self) -> None:
        """Initialize all pipeline components."""
        self.ser_ensemble = SEREnsemble(use_dummy=True)
        self.emotion_mapper = EmotionMapper()
        self.intervention_selector = InterventionSelector()
        self.llm_chain = FallbackChain()
        self.spotify = SpotifyClient()
        self.tmdb = TMDBClient()
        self.lighting = LightingClient()
        self.audio_capture = AudioCapture(
            sample_rate=self.config.sample_rate_hz,
            window_seconds=self.config.audio_window_seconds,
        )
        self._initialized = True
        logger.info("MoodWeaverPipeline initialized (dummy SER mode)")

    async def process_ser_result(self, ser_probs: dict[str, float], confidence: float) -> EmotionState:
        """Convert SER probabilities to an EmotionState."""
        assert self.emotion_mapper is not None
        return self.emotion_mapper.map_from_ser_probabilities(ser_probs, confidence)

    async def generate_mashup(self, emotion: EmotionState) -> MashupResult:
        """Run the full mashup generation pipeline for a given emotion state."""
        assert self.llm_chain is not None
        assert self.spotify is not None
        assert self.tmdb is not None
        assert self.lighting is not None
        assert self.intervention_selector is not None

        start = time.perf_counter()
        profile = get_user_preferences()

        # 1. Select intervention mode
        mode = self.intervention_selector.select(emotion)

        # 2. Generate mashup spec via LLM fallback chain
        user_profile = UserProfile(preferences=profile)
        spec: MashupSpec = await self.llm_chain.generate(emotion, user_profile, mode)

        # 3. Fetch content from APIs in parallel
        movie_task = self.tmdb.search_movies(spec.film_query, limit=3)
        playlist_task = self.spotify.search_playlists(
            spec.music_query,
            tempo_range=(spec.light_scene.color_temperature, spec.light_scene.brightness),
            limit=3,
        )

        movie_results, playlist_results = await asyncio.gather(movie_task, playlist_task)

        spec.movie = movie_results[0] if movie_results else None
        spec.playlists = playlist_results

        # 4. Activate lighting (fire-and-forget)
        if self.config.enable_lighting:
            asyncio.create_task(self.lighting.activate_scene(spec.light_scene))

        elapsed = (time.perf_counter() - start) * 1000

        # 5. Persist
        record_mood(
            valence=emotion.va.valence,
            arousal=emotion.va.arousal,
            label=emotion.label,
            confidence=emotion.confidence,
            source=emotion.source,
        )
        log_mashup(spec, emotion.label.value, emotion.va.valence, emotion.va.arousal)

        return MashupResult(
            spec=spec,
            emotion_state=emotion,
            pipeline_ms=round(elapsed, 1),
        )

    async def process_audio_chunk(self, chunk: AudioChunk) -> MashupResult:
        """Full pipeline: audio chunk → emotion → mashup."""
        assert self.ser_ensemble is not None

        ser_result = self.ser_ensemble.analyze(chunk)
        emotion = await self.process_ser_result(
            ser_result.emotion_label.value,
            ser_result.confidence,
        )
        # Override with actual VA from the ensemble
        emotion = EmotionState(
            va=ser_result.va,
            label=ser_result.emotion_label,
            confidence=ser_result.confidence,
        )
        return await self.generate_mashup(emotion)

    async def run_continuous(self, on_mashup: Callable[[MashupResult], None]) -> None:
        """Run the pipeline in continuous mode — captures audio and generates mashups."""
        assert self.audio_capture is not None
        assert self._initialized

        def _on_chunk(chunk: AudioChunk) -> None:
            """Synchronous callback from audio capture → schedule async pipeline."""
            asyncio.ensure_future(self._handle_chunk(chunk, on_mashup))

        self.audio_capture.start(on_chunk=_on_chunk)
        logger.info("Continuous pipeline started — listening for audio")

    async def _handle_chunk(self, chunk: AudioChunk, on_mashup: Callable[[MashupResult], None]) -> None:
        """Process a single audio chunk and invoke the mashup callback."""
        try:
            result = await self.process_audio_chunk(chunk)
            on_mashup(result)
        except Exception as e:
            logger.error(f"Pipeline error processing chunk: {e}")

    def stop(self) -> None:
        """Stop continuous audio capture."""
        if self.audio_capture:
            self.audio_capture.stop()
            logger.info("Continuous pipeline stopped")
