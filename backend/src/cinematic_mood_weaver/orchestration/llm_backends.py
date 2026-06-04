"""Pluggable LLM backends with a 4-tier fallback chain.

Claude API → GPT-4 API → local Ollama → rule-based template fallback.
Each backend implements the LLMBackend protocol and returns a validated MashupSpec.
"""

from __future__ import annotations

import json
import logging
import random
from abc import ABC, abstractmethod
from typing import Optional, Protocol, runtime_checkable

from cinematic_mood_weaver.config import settings
from cinematic_mood_weaver.types.models import (
    DiffuserSchedule,
    EmotionState,
    InterventionMode,
    LightScene,
    MashupSpec,
    UserProfile,
)

logger = logging.getLogger(__name__)


# ── Prompt Template ───────────────────────────────────────────────────


MASHUP_SYSTEM_PROMPT = """You are the Cinematic Mood Weaver — an AI entertainment director that creates personalized multi-sensory experiences based on real-time emotional state.

You receive the user's current emotional state, mood history, and preferences.
Your job is to produce a structured JSON mashup specification that coordinates:
1. A movie/TV show recommendation (film_query)
2. A music playlist recommendation (music_query with seed genres, tempo range, valence)
3. A smart lighting scene (warm/cool, brightness)
4. An aromatherapy diffuser profile (optional)
5. A short narrative message explaining your curation

Rules:
- Mirror mode: match recommendations to the current mood
- Nudge mode: gently guide toward a more positive/calm state
- Transform mode: strongly redirect toward a target mood
- Keep narratives warm, empathetic, and concise (1-2 sentences)
- Music tempo: relaxing <80 BPM, moderate 80-120 BPM, energetic >120 BPM
- Lighting: warm (2700-3500K) for calm, cool (5000-6500K) for energy
- Respond ONLY with valid JSON, no other text."""


def _build_context(emotion: EmotionState, profile: UserProfile, mode: InterventionMode) -> str:
    """Build the user context JSON block that's sent to the LLM."""
    recent = [m.label.value for m in profile.recent_moods[-10:]]
    return json.dumps({
        "emotion": {
            "valence": emotion.va.valence,
            "arousal": emotion.va.arousal,
            "label": emotion.label.value,
            "confidence": emotion.confidence,
        },
        "mood_history": recent,
        "intervention_mode": mode.value,
        "user_preferences": {
            "genres": profile.preferences.preferred_genres,
            "disliked": profile.preferences.disliked_genres,
        },
        "available_devices": profile.preferences.available_devices,
        "time_of_day": _time_of_day(),
    })


def _time_of_day() -> str:
    from datetime import datetime
    h = datetime.now().hour
    if h < 12:
        return "morning"
    if h < 17:
        return "afternoon"
    if h < 22:
        return "evening"
    return "night"


# ── Backend Protocol ──────────────────────────────────────────────────


@runtime_checkable
class LLMBackend(Protocol):
    """Protocol that all LLM backends must implement."""

    async def generate_mashup_spec(self, emotion: EmotionState, profile: UserProfile, mode: InterventionMode) -> MashupSpec:
        ...


# ── Claude Backend ────────────────────────────────────────────────────


class ClaudeBackend:
    """Anthropic Claude API backend for mashup generation."""

    def __init__(self):
        self._client: Optional[object] = None

    def _ensure_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=settings.claude_api_key)

    async def generate_mashup_spec(self, emotion: EmotionState, profile: UserProfile, mode: InterventionMode) -> MashupSpec:
        """Call Claude API and parse the structured response."""
        self._ensure_client()
        context = _build_context(emotion, profile, mode)

        import anthropic
        assert self._client is not None
        response = self._client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=MASHUP_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Generate a mashup for this emotional context:\n{context}"}],
        )

        raw = response.content[0].text if response.content else "{}"
        return _parse_to_mashup_spec(raw, emotion, mode)


# ── OpenAI GPT-4 Backend ──────────────────────────────────────────────


class GPT4Backend:
    """OpenAI GPT-4 backend as the primary fallback."""

    def __init__(self):
        self._client: Optional[object] = None

    def _ensure_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=settings.openai_api_key)

    async def generate_mashup_spec(self, emotion: EmotionState, profile: UserProfile, mode: InterventionMode) -> MashupSpec:
        """Call GPT-4 API and parse the structured response."""
        self._ensure_client()
        context = _build_context(emotion, profile, mode)

        from openai import OpenAI
        assert self._client is not None
        response = self._client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1024,
            temperature=0.7,
            messages=[
                {"role": "system", "content": MASHUP_SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate a mashup for this emotional context:\n{context}"},
            ],
        )

        raw = response.choices[0].message.content or "{}"
        return _parse_to_mashup_spec(raw, emotion, mode)


# ── Ollama Backend ────────────────────────────────────────────────────


class OllamaBackend:
    """Local Ollama (Mistral 7B) backend for offline LLM fallback."""

    def __init__(self, base_url: str = ""):
        self.base_url = base_url or settings.ollama_base_url

    async def generate_mashup_spec(self, emotion: EmotionState, profile: UserProfile, mode: InterventionMode) -> MashupSpec:
        """Call local Ollama and parse the structured response."""
        import aiohttp

        context = _build_context(emotion, profile, mode)
        payload = {
            "model": "mistral:7b",
            "prompt": f"{MASHUP_SYSTEM_PROMPT}\n\nGenerate a mashup for: {context}\n\nJSON:",
            "stream": False,
            "format": "json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/generate", json=payload) as resp:
                data = await resp.json()
                raw = data.get("response", "{}")

        return _parse_to_mashup_spec(raw, emotion, mode)


# ── Template Fallback (guaranteed offline operation) ──────────────────


class TemplateFallback:
    """Rule-based mashup generator — guaranteed to work with no LLM dependency."""

    # Mood → content mapping
    MOOD_MAP = {
        "happy": {
            "narrative": "You're feeling great! Let's keep that energy going with something uplifting.",
            "film_query": "feel good comedy adventure",
            "music_query": "happy upbeat pop",
            "music_tempo": (120, 150),
            "lighting": ("energizing", 5000, 200),
            "diffuser": "citrus",
        },
        "calm": {
            "narrative": "You're in a peaceful state. Here's something soothing to match your calm.",
            "film_query": "relaxing nature documentary",
            "music_query": "ambient chill lo-fi",
            "music_tempo": (60, 80),
            "lighting": ("relaxing", 3000, 120),
            "diffuser": "lavender",
        },
        "sad": {
            "narrative": "It's okay to feel this way. Here's a gentle experience to comfort you.",
            "film_query": "heartwarming drama comfort",
            "music_query": "acoustic singer songwriter",
            "music_tempo": (70, 90),
            "lighting": ("warm", 2700, 100),
            "diffuser": "vanilla",
        },
        "angry": {
            "narrative": "Let's release that tension. Here's something intense to match your energy, then we'll wind down.",
            "film_query": "action thriller high energy",
            "music_query": "rock metal high energy",
            "music_tempo": (140, 180),
            "lighting": ("cool", 6000, 220),
            "diffuser": "peppermint",
        },
        "anxious": {
            "narrative": "Take a deep breath. Let's bring that energy down with something grounding.",
            "film_query": "mindful calming documentary",
            "music_query": "ambient nature sounds meditation",
            "music_tempo": (50, 70),
            "lighting": ("calming", 3500, 80),
            "diffuser": "chamomile",
        },
        "neutral": {
            "narrative": "Let's find something that resonates with your current headspace.",
            "film_query": "critically acclaimed popular",
            "music_query": "eclectic curated mix",
            "music_tempo": (90, 120),
            "lighting": ("balanced", 4000, 150),
            "diffuser": "eucalyptus",
        },
        "surprised": {
            "narrative": "Let's keep that spark of discovery going with something unexpected.",
            "film_query": "mind bending twist unique",
            "music_query": "experimental eclectic",
            "music_tempo": (100, 140),
            "lighting": ("vibrant", 4500, 180),
            "diffuser": "mint",
        },
        "fearful": {
            "narrative": "You're safe here. Let's find something comforting to ease your mind.",
            "film_query": "lighthearted comedy comfort",
            "music_query": "soft piano acoustic",
            "music_tempo": (60, 80),
            "lighting": ("warm", 2700, 90),
            "diffuser": "lavender",
        },
        "disgust": {
            "narrative": "Let's reset with something clean and refreshing.",
            "film_query": "beautiful cinematography travel",
            "music_query": "fresh indie uplifting",
            "music_tempo": (80, 110),
            "lighting": ("fresh", 5000, 160),
            "diffuser": "eucalyptus",
        },
    }

    DEFAULT = MOOD_MAP["neutral"]

    async def generate_mashup_spec(self, emotion: EmotionState, profile: UserProfile, mode: InterventionMode) -> MashupSpec:
        """Generate a mashup using rule-based mood → content mapping."""
        del profile
        config = self.MOOD_MAP.get(emotion.label.value, self.DEFAULT)

        if mode == InterventionMode.NUDGE:
            # For nudge mode, shift toward a more positive config
            config = self.MOOD_MAP.get("calm", self.DEFAULT)
        elif mode == InterventionMode.TRANSFORM:
            config = self.MOOD_MAP.get("happy", self.DEFAULT)

        return MashupSpec(
            mood_target=emotion.label.value,
            intervention_mode=mode,
            narrative=config["narrative"],
            film_query=config["film_query"],
            music_query=config["music_query"],
            light_scene=LightScene(
                scene_name=config["lighting"][0],
                color_temperature=config["lighting"][1],
                brightness=config["lighting"][2],
            ),
            diffuser_profile=DiffuserSchedule(oil_profile=config["diffuser"]),
        )


# ── Mashup Spec Parser ────────────────────────────────────────────────


def _parse_to_mashup_spec(raw: str, emotion: EmotionState, mode: InterventionMode) -> MashupSpec:
    """Parse raw LLM output string into a validated MashupSpec.

    Falls back to TemplateFallback if parsing fails.
    """
    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("\n```", 1)[0]
    if raw.startswith("```json"):
        raw = raw[7:].strip()

    try:
        data = json.loads(raw)
        return MashupSpec(
            mood_target=data.get("mood_target", emotion.label.value),
            intervention_mode=mode,
            narrative=data.get("narrative", "Enjoy your personalized experience!"),
            film_query=data.get("film_query", "popular"),
            music_query=data.get("music_query", "mood mix"),
            light_scene=LightScene(
                scene_name=data.get("light_scene", {}).get("scene_name", "balanced"),
                brightness=data.get("light_scene", {}).get("brightness", 128),
                color_temperature=data.get("light_scene", {}).get("color_temperature", 3500),
            ),
            diffuser_profile=DiffuserSchedule(
                oil_profile=data.get("diffuser_profile", {}).get("oil_profile", "lavender"),
            ),
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Failed to parse LLM output, using template fallback: {e}")
        fallback = TemplateFallback()
        import asyncio
        return asyncio.run(fallback.generate_mashup_spec(emotion, UserProfile(), mode))


# ── Fallback Chain ────────────────────────────────────────────────────


class FallbackChain:
    """4-tier fallback chain for mashup generation.

    1. Claude API
    2. GPT-4 API
    3. Ollama (local)
    4. Template (rule-based, always works)
    """

    def __init__(self):
        self._backends = [
            ("claude", ClaudeBackend()),
            ("openai", GPT4Backend()),
            ("ollama", OllamaBackend()),
            ("template", TemplateFallback()),
        ]

    async def generate(self, emotion: EmotionState, profile: UserProfile, mode: InterventionMode) -> MashupSpec:
        """Try each backend in order until one succeeds."""
        last_error: Optional[Exception] = None

        for name, backend in self._backends:
            if name == "claude" and not settings.claude_api_key:
                continue
            if name == "openai" and not settings.openai_api_key:
                continue
            if name == "ollama" and not settings.ollama_base_url:
                continue

            try:
                spec = await backend.generate_mashup_spec(emotion, profile, mode)
                logger.info(f"Mashup generated by backend: {name}")
                return spec
            except Exception as e:
                logger.warning(f"Backend '{name}' failed: {e}")
                last_error = e
                continue

        # All backends failed — this shouldn't happen since TemplateFallback always works
        raise RuntimeError("All LLM backends failed") from last_error
