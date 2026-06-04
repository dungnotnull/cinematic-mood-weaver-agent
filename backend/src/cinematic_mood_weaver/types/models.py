"""Pydantic models for the cinematic-mood-weaver data domain.

Emotion state representation uses Russell's circumplex model (valence-arousal 2D space),
and the mashup spec is the structured output from the LLM orchestration layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Emotion Domain ──────────────────────────────────────────────────────────


class EmotionLabel(str, Enum):
    """Discrete emotion labels mapped from valence-arousal coordinates."""

    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    NEUTRAL = "neutral"
    ANXIOUS = "anxious"
    CALM = "calm"
    SURPRISED = "surprised"
    DISGUST = "disgust"
    FEARFUL = "fearful"


class ValenceArousal(BaseModel):
    """2D emotion representation (Russell's circumplex model).

    - Valence: -1 (very negative) to +1 (very positive)
    - Arousal: -1 (very calm/deactivated) to +1 (very excited/activated)
    """

    valence: float = Field(..., ge=-1.0, le=1.0)
    arousal: float = Field(..., ge=-1.0, le=1.0)


class EmotionState(BaseModel):
    """Full emotion inference result from the sensing pipeline."""

    va: ValenceArousal
    label: EmotionLabel
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = Field(default="ser")  # "ser" | "biometric" | "fusion" | "manual"


class EmotionHistoryEntry(BaseModel):
    """A single row from the mood_history table, for API/LLM context."""

    id: int
    timestamp: datetime
    valence: float
    arousal: float
    label: EmotionLabel
    confidence: float
    source: str


class SerModelOutput(BaseModel):
    """Raw output from a wav2vec2 SER model."""

    model_id: str
    class_probabilities: dict[str, float]
    inference_ms: float


# ── Intervention Domain ──────────────────────────────────────────────────────


class InterventionMode(str, Enum):
    """Three-tier mood intervention system."""

    MIRROR = "mirror"  # Match current mood
    NUDGE = "nudge"  # Gentle shift toward more positive state
    TRANSFORM = "transform"  # Strong redirect toward target mood


# ── User Profile ─────────────────────────────────────────────────────────────


class UserPreferences(BaseModel):
    """User's content preferences, learned from feedback over time."""

    preferred_genres: list[str] = Field(default_factory=list)
    disliked_genres: list[str] = Field(default_factory=list)
    preferred_arousal_range: tuple[float, float] = Field(default=(-1.0, 1.0))
    session_duration_minutes: int = Field(default=90)
    available_devices: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    """Aggregated user context for LLM orchestration."""

    user_id: str = Field(default="default")
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    recent_moods: list[EmotionHistoryEntry] = Field(default_factory=list)
    target_mood: Optional[ValenceArousal] = None


# ── Content Domain ───────────────────────────────────────────────────────────


class MovieRecommendation(BaseModel):
    """A single movie or TV show recommendation from TMDB/JustWatch."""

    title: str
    year: int
    overview: str
    poster_url: str
    tmdb_id: int
    media_type: str = Field(default="movie")  # "movie" | "tv"
    genre_ids: list[int] = Field(default_factory=list)
    vote_average: float = Field(default=0.0)
    streaming_url: Optional[str] = None


class PlaylistRecommendation(BaseModel):
    """A Spotify playlist recommendation."""

    name: str
    spotify_id: str
    url: str
    track_count: int = Field(default=0)
    tempo_range: tuple[int, int] = Field(default=(0, 200))
    valence_target: float = Field(default=0.0)
    image_url: Optional[str] = None


class LightScene(BaseModel):
    """Smart lighting configuration for the mashup."""

    scene_name: str
    brightness: int = Field(default=128, ge=0, le=254)
    color_temperature: int = Field(default=3500, ge=2000, le=6500)
    transition_ms: int = Field(default=1000)


class DiffuserSchedule(BaseModel):
    """Aromatherapy diffuser schedule."""

    oil_profile: str = Field(default="lavender")
    duration_minutes: int = Field(default=30)
    intensity: int = Field(default=3, ge=1, le=5)


# ── Mashup Domain ────────────────────────────────────────────────────────────


class MashupSpec(BaseModel):
    """The structured output from the LLM orchestration layer.

    This is the core data structure that drives the entire content & environment layer.
    """

    mood_target: str = Field(..., description="Brief description of the mood goal")
    intervention_mode: InterventionMode
    narrative: str = Field(..., description="LLM-generated narrative for the UI card")
    film_query: str = Field(..., description="TMDB search query or genre description")
    music_query: str = Field(..., description="Spotify seed genres / tempo / valence")
    light_scene: LightScene = Field(default_factory=LightScene)
    diffuser_profile: DiffuserSchedule = Field(default_factory=DiffuserSchedule)

    # Filled by API clients after the spec is generated
    movie: Optional[MovieRecommendation] = None
    playlists: list[PlaylistRecommendation] = Field(default_factory=list)
    available_devices: list[str] = Field(default_factory=list)


class MashupResult(BaseModel):
    """The fully populated mashup after all API calls complete."""

    spec: MashupSpec
    emotion_state: EmotionState
    generated_at: datetime = Field(default_factory=datetime.now)
    pipeline_ms: float = Field(default=0.0)


# ── API / Pipeline DTOs ────────────────────────────────────────────────


class PipelineConfig(BaseModel):
    """Runtime configuration for the main pipeline loop."""

    audio_window_seconds: float = Field(default=3.0, gt=0)
    sample_rate_hz: int = Field(default=16000)
    ser_poll_interval_seconds: int = Field(default=300)
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    enable_biometrics: bool = Field(default=False)
    enable_lighting: bool = Field(default=True)
    enable_aromatherapy: bool = Field(default=False)
    intervention_mode_default: InterventionMode = Field(default=InterventionMode.MIRROR)
