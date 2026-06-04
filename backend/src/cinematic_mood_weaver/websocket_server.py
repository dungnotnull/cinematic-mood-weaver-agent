"""Real-time WebSocket server — bridges Python backend to Tauri frontend.

Pushes live emotion state updates and mashup results to connected clients.
Receives commands: run_mashup, set_feedback, mood_override, get_history.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Callable, Optional

from cinematic_mood_weaver.db.service import (
    get_mood_history_since,
    get_recent_moods,
    rate_mashup,
    record_mood,
)
from cinematic_mood_weaver.pipeline import MoodWeaverPipeline
from cinematic_mood_weaver.types.models import EmotionState, MashupResult, UserPreferences

logger = logging.getLogger(__name__)

COMMANDS: dict[str, Callable] = {}


def register(name: str):
    """Decorator to register a WebSocket command handler."""
    def wrapper(fn):
        COMMANDS[name] = fn
        return fn
    return wrapper


class WebSocketServer:
    """Asynchronous WebSocket server using aiohttp.

    Runs on a configurable port (default 9876) and accepts connections
    from the Tauri frontend. Maintains a set of connected clients.
    """

    def __init__(self, pipeline: MoodWeaverPipeline, host: str = "127.0.0.1", port: int = 9876):
        self.pipeline = pipeline
        self.host = host
        self.port = port
        self._sockets: list[Any] = []
        self._app: Optional[Any] = None
        self._runner: Optional[Any] = None
        self._site: Optional[Any] = None
        self._command_handlers: dict[str, Callable] = {}

    async def broadcast(self, event: str, data: dict[str, Any]) -> None:
        """Send a JSON message to all connected clients."""
        payload = json.dumps({"event": event, "data": data, "timestamp": time.time()})
        dead: list[Any] = []
        for ws in self._sockets:
            try:
                await ws.send_str(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._sockets.remove(ws)

    async def broadcast_mood(self, emotion: EmotionState) -> None:
        """Push live emotion state update to all clients."""
        await self.broadcast("mood_update", {
            "va": {"valence": emotion.va.valence, "arousal": emotion.va.arousal},
            "label": emotion.label.value,
            "confidence": emotion.confidence,
            "source": emotion.source,
            "timestamp": emotion.timestamp.isoformat(),
        })

    async def broadcast_mashup(self, result: MashupResult) -> None:
        """Push a completed mashup to all clients."""
        await self.broadcast("mashup_result", result.model_dump(mode="json"))

    async def _handle_ws(self, request: Any) -> Any:
        """Handle an incoming WebSocket connection."""
        from aiohttp import web
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._sockets.append(ws)
        peer = request.remote
        logger.info(f"WebSocket client connected: {peer}")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self._handle_message(ws, msg.data)
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
        except Exception:
            pass
        finally:
            self._sockets.remove(ws)
            logger.info(f"WebSocket client disconnected: {peer}")

        return ws

    async def _handle_message(self, ws: Any, raw: str) -> None:
        """Parse and dispatch an incoming command."""
        try:
            data = json.loads(raw)
            command = data.get("command", "")
            payload = data.get("payload", {})
            msg_id = data.get("id", "")
        except json.JSONDecodeError:
            return

        handler = COMMANDS.get(command)
        if handler is None:
            logger.warning(f"Unknown command: {command}")
            return

        try:
            result = await handler(self, payload)
            await ws.send_str(json.dumps({"id": msg_id, "result": result}))
        except Exception as e:
            await ws.send_str(json.dumps({"id": msg_id, "error": str(e)}))
            logger.error(f"Command '{command}' failed: {e}")

    async def start(self) -> None:
        """Start the WebSocket server."""
        from aiohttp import web
        self._app = web.Application()
        self._app.router.add_get("/ws", self._handle_ws)

        # Health endpoint
        async def health(_request):
            return web.json_response({
                "status": "ok",
                "clients": len(self._sockets),
                "pipeline_initialized": self.pipeline._initialized,
            })
        self._app.router.add_get("/health", health)

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()
        logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Gracefully stop the WebSocket server."""
        for ws in list(self._sockets):
            try:
                await ws.close()
            except Exception:
                pass
        self._sockets.clear()
        if self._runner:
            await self._runner.cleanup()
            logger.info("WebSocket server stopped")


# ── Command Handlers ─────────────────────────────────────────────────


@register("run_mashup")
async def cmd_run_mashup(server: WebSocketServer, payload: dict) -> dict:
    """Generate a mashup from current mood context and return results."""
    from cinematic_mood_weaver.emotion.emotion_mapper import EmotionMapper
    from cinematic_mood_weaver.types.models import ValenceArousal

    # If an emotion state is provided, use it; otherwise simulate
    if "emotion" in payload:
        e = payload["emotion"]
        mapper = EmotionMapper()
        emotion = mapper.map_from_va(
            ValenceArousal(valence=e.get("valence", 0), arousal=e.get("arousal", 0)),
            confidence=e.get("confidence", 0.8),
            source=e.get("source", "manual"),
        )
    else:
        mapper = EmotionMapper()
        emotion = mapper.map_from_va(
            ValenceArousal(valence=payload.get("valence", 0), arousal=payload.get("arousal", 0)),
            confidence=0.8,
        )

    result = await server.pipeline.generate_mashup(emotion)
    await server.broadcast_mashup(result)
    return result.model_dump(mode="json")


@register("get_history")
async def cmd_get_history(server: WebSocketServer, payload: dict) -> list:
    """Fetch recent mood history."""
    limit = payload.get("limit", 50)
    entries = get_recent_moods(limit=limit)
    return [e.model_dump(mode="json") for e in entries]


@register("set_feedback")
async def cmd_set_feedback(server: WebSocketServer, payload: dict) -> dict:
    """Record user feedback (thumbs up/down) for a mashup."""
    mashup_id = payload.get("mashup_id")
    rating = payload.get("rating")  # -1, 0, 1 mapped to 1-5
    if mashup_id and rating is not None:
        mapped = {1: 5, 0: 3, -1: 1}.get(rating, 3)
        ok = rate_mashup(mashup_id, mapped)
        await server.broadcast("feedback_recorded", {"mashup_id": mashup_id, "rating": rating})
        return {"ok": ok}
    return {"ok": False, "error": "mashup_id and rating required"}


@register("mood_override")
async def cmd_mood_override(server: WebSocketServer, payload: dict) -> dict:
    """Allow user to manually override their detected emotion."""
    label = payload.get("label", "neutral")
    valence = payload.get("valence", 0.0)
    arousal = payload.get("arousal", 0.0)

    from cinematic_mood_weaver.db.service import record_mood
    from cinematic_mood_weaver.types.models import EmotionLabel
    emotion_label = EmotionLabel(label) if label in [e.value for e in EmotionLabel] else EmotionLabel.NEUTRAL

    record_mood(valence=valence, arousal=arousal, label=emotion_label, confidence=1.0, source="manual")

    mapper = EmotionMapper()
    emotion = mapper.map_from_va(ValenceArousal(valence=valence, arousal=arousal), confidence=1.0, source="manual")
    await server.broadcast_mood(emotion)
    return {"ok": True}


@register("health")
async def cmd_health(server: WebSocketServer, payload: dict) -> dict:
    """Return server health status."""
    return {
        "status": "ok",
        "clients": len(server._sockets),
        "pipeline_initialized": server.pipeline._initialized,
    }
