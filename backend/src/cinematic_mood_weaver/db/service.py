"""CRUD service for the Cinematic Mood Weaver database.

Provides high-level read/write operations for mood history, user preferences,
mashup logs, and encryption of sensitive fields.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import desc

from cinematic_mood_weaver.config import settings
from cinematic_mood_weaver.db.engine import get_session
from cinematic_mood_weaver.db.models import MashupLog, MoodHistory, UserPreference
from cinematic_mood_weaver.types.models import (
    EmotionHistoryEntry,
    EmotionLabel,
    InterventionMode,
    MashupSpec,
    UserPreferences,
)
from cinematic_mood_weaver.utils.encryption import decrypt_text, encrypt_text


# ── Mood History ──────────────────────────────────────────────────────


def record_mood(valence: float, arousal: float, label: EmotionLabel, confidence: float, source: str = "ser") -> int:
    """Insert a new mood history row. Returns the row id."""
    session_factory = get_session()
    with session_factory() as session:
        entry = MoodHistory(
            valence=valence,
            arousal=arousal,
            label=label.value,
            confidence=confidence,
            source=source,
        )
        session.add(entry)
        session.commit()
        return entry.id


def get_recent_moods(limit: int = 50) -> list[EmotionHistoryEntry]:
    """Fetch the most recent N mood history entries, newest first."""
    session_factory = get_session()
    with session_factory() as session:
        rows = (
            session.query(MoodHistory)
            .order_by(desc(MoodHistory.timestamp))
            .limit(limit)
            .all()
        )
        return [
            EmotionHistoryEntry(
                id=r.id,
                timestamp=r.timestamp,
                valence=r.valence,
                arousal=r.arousal,
                label=EmotionLabel(r.label),
                confidence=r.confidence,
                source=r.source,
            )
            for r in rows
        ]


def get_mood_history_since(hours: int = 24) -> list[EmotionHistoryEntry]:
    """Fetch mood history from the last N hours, oldest first (for trend analysis)."""
    cutoff = datetime.now() - timedelta(hours=hours)
    session_factory = get_session()
    with session_factory() as session:
        rows = (
            session.query(MoodHistory)
            .filter(MoodHistory.timestamp >= cutoff)
            .order_by(MoodHistory.timestamp)
            .all()
        )
        return [
            EmotionHistoryEntry(
                id=r.id,
                timestamp=r.timestamp,
                valence=r.valence,
                arousal=r.arousal,
                label=EmotionLabel(r.label),
                confidence=r.confidence,
                source=r.source,
            )
            for r in rows
        ]


# ── User Preferences ──────────────────────────────────────────────────


def get_user_preferences() -> UserPreferences:
    """Load user preferences from the DB. Returns defaults if none exist."""
    session_factory = get_session()
    with session_factory() as session:
        rows = session.query(UserPreference).all()
    prefs_dict: dict[str, str] = {r.key: r.value for r in rows}
    return _deserialize_preferences(prefs_dict)


def save_user_preferences(prefs: UserPreferences) -> None:
    """Persist user preferences to the DB, overwriting existing keys."""
    serialized = _serialize_preferences(prefs)
    session_factory = get_session()
    with session_factory() as session:
        for key, value in serialized.items():
            existing = session.query(UserPreference).filter(UserPreference.key == key).first()
            if existing:
                existing.value = value
            else:
                session.add(UserPreference(key=key, value=value))
        session.commit()


def _serialize_preferences(prefs: UserPreferences) -> dict[str, str]:
    return {
        "preferred_genres": json.dumps(prefs.preferred_genres),
        "disliked_genres": json.dumps(prefs.disliked_genres),
        "preferred_arousal_range": json.dumps(list(prefs.preferred_arousal_range)),
        "session_duration_minutes": str(prefs.session_duration_minutes),
        "available_devices": json.dumps(prefs.available_devices),
    }


def _deserialize_preferences(data: dict[str, str]) -> UserPreferences:
    return UserPreferences(
        preferred_genres=json.loads(data.get("preferred_genres", "[]")),
        disliked_genres=json.loads(data.get("disliked_genres", "[]")),
        preferred_arousal_range=tuple(
            json.loads(data.get("preferred_arousal_range", "[-1.0, 1.0]"))
        ),
        session_duration_minutes=int(data.get("session_duration_minutes", "90")),
        available_devices=json.loads(data.get("available_devices", "[]")),
    )


# ── Mashup Log ────────────────────────────────────────────────────────


def log_mashup(
    spec: MashupSpec,
    emotion_label: str,
    valence: float,
    arousal: float,
) -> int:
    """Record a generated mashup in the log. Returns the row id."""
    session_factory = get_session()
    with session_factory() as session:
        entry = MashupLog(
            emotion_label=emotion_label,
            valence=valence,
            arousal=arousal,
            intervention_mode=spec.intervention_mode.value,
            narrative=spec.narrative,
            movie_title=spec.movie.title if spec.movie else None,
            playlist_name=spec.playlists[0].name if spec.playlists else None,
            light_scene=spec.light_scene.scene_name,
        )
        session.add(entry)
        session.commit()
        return entry.id


def rate_mashup(mashup_id: int, rating: int) -> bool:
    """Set user rating (1-5) for a previously generated mashup."""
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")
    session_factory = get_session()
    with session_factory() as session:
        entry = session.query(MashupLog).filter(MashupLog.id == mashup_id).first()
        if not entry:
            return False
        entry.user_rating = rating
        session.commit()
        return True
