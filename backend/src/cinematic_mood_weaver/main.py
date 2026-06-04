"""Entry point for the Cinematic Mood Weaver Agent.

Supports two modes:
  - demo:   Single demo cycle with synthetic data (default)
  - server: Launch WebSocket server + pipeline for frontend connectivity
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from cinematic_mood_weaver.config import settings
from cinematic_mood_weaver.db.engine import init_db
from cinematic_mood_weaver.pipeline import MoodWeaverPipeline
from cinematic_mood_weaver.utils.logging_setup import setup_logging
from cinematic_mood_weaver.utils.scheduler import PipelineScheduler
from cinematic_mood_weaver.websocket_server import WebSocketServer

logger = logging.getLogger(__name__)


async def demo_cycle(pipeline: MoodWeaverPipeline) -> None:
    """Run a single demo mashup cycle using synthetic emotion data."""
    logger.info("=" * 60)
    logger.info("CINEMATIC MOOD WEAVER — Demo Cycle")
    logger.info("=" * 60)

    from cinematic_mood_weaver.emotion.emotion_mapper import EmotionMapper
    from cinematic_mood_weaver.types.models import ValenceArousal

    mapper = EmotionMapper()
    emotion = mapper.map_from_va(ValenceArousal(valence=-0.4, arousal=0.7), confidence=0.85)
    logger.info(f"Simulated emotion: {emotion.label.value} "
                f"(v={emotion.va.valence:.2f}, a={emotion.va.arousal:.2f}, "
                f"conf={emotion.confidence:.2f})")

    result = await pipeline.generate_mashup(emotion)
    logger.info(f"Mashup generated in {result.pipeline_ms:.0f}ms")
    logger.info(f"  Narrative: {result.spec.narrative}")
    logger.info(f"  Film query: {result.spec.film_query}")
    logger.info(f"  Music query: {result.spec.music_query}")
    logger.info(f"  Light scene: {result.spec.light_scene.scene_name} "
                f"(CT={result.spec.light_scene.color_temperature}K, "
                f"bri={result.spec.light_scene.brightness})")
    logger.info(f"  Diffuser: {result.spec.diffuser_profile.oil_profile}")
    if result.spec.movie:
        logger.info(f"  Movie: {result.spec.movie.title} ({result.spec.movie.vote_average}/10)")
    if result.spec.playlists:
        logger.info(f"  Playlist: {result.spec.playlists[0].name}")
    logger.info("= Demo cycle complete =\n")


async def run_server() -> None:
    """Launch the full server with WebSocket + pipeline + scheduler."""
    setup_logging()
    logger.info("Cinematic Mood Weaver v0.1.0 — SERVER MODE")

    init_db()
    logger.info("Database initialized")

    pipeline = MoodWeaverPipeline()
    await pipeline.initialize()

    ws_server = WebSocketServer(pipeline, port=9876)
    await ws_server.start()

    scheduler = PipelineScheduler()
    scheduler.start()

    logger.info("=" * 56)
    logger.info("  Server ready! Connect frontend to ws://127.0.0.1:9876/ws")
    logger.info("  Health: http://127.0.0.1:9876/health")
    logger.info("=" * 56)

    try:
        await asyncio.Event().wait()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        scheduler.stop()
        await ws_server.stop()


async def run_demo() -> None:
    """Initialize everything and run a demo cycle."""
    setup_logging()
    logger.info("Cinematic Mood Weaver v0.1.0 — DEMO MODE")
    logger.info(f"Config: db={settings.db_path}, SER model={settings.ser_model_primary}")

    init_db()
    logger.info("Database initialized")

    pipeline = MoodWeaverPipeline()
    await pipeline.initialize()
    await demo_cycle(pipeline)

    logger.info("Demo completed successfully.")
    logger.info("To run as server: python -m cinematic_mood_weaver.main --mode server")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Cinematic Mood Weaver Agent")
    parser.add_argument("--mode", type=str, default="demo", choices=["demo", "server"],
                        help="Run mode: demo (single cycle) or server (WebSocket + pipeline)")
    args = parser.parse_args()

    if args.mode == "server":
        asyncio.run(run_server())
    else:
        asyncio.run(run_demo())


if __name__ == "__main__":
    main()
