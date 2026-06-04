"""SQLAlchemy ORM models for Cinematic Mood Weaver persistence layer."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from .engine import Base


class MoodHistory(Base):
    """Stores each emotion inference result with timestamp."""

    __tablename__ = "mood_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)
    valence = Column(Float, nullable=False)
    arousal = Column(Float, nullable=False)
    label = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False)
    source = Column(String(32), default="ser", nullable=False)

    def __repr__(self) -> str:
        return (
            f"<MoodHistory(id={self.id}, label={self.label}, "
            f"valence={self.valence:.2f}, arousal={self.arousal:.2f}, "
            f"confidence={self.confidence:.2f})>"
        )


class UserPreference(Base):
    """Key-value store for user preferences, learned weights, and settings."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        truncated = self.value[:40] + "..." if len(self.value) > 40 else self.value
        return f"<UserPreference(key={self.key}, value={truncated})>"


class MashupLog(Base):
    """Log of every generated mashup for history, analytics, and re-creation."""

    __tablename__ = "mashup_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    emotion_label = Column(String(32), nullable=False)
    valence = Column(Float, nullable=False)
    arousal = Column(Float, nullable=False)
    intervention_mode = Column(String(16), nullable=False)
    narrative = Column(Text, nullable=True)
    movie_title = Column(String(256), nullable=True)
    playlist_name = Column(String(256), nullable=True)
    light_scene = Column(String(64), nullable=True)
    user_rating = Column(Integer, nullable=True)  # 1-5 stars, null = unrated

    def __repr__(self) -> str:
        return f"<MashupLog(id={self.id}, emotion={self.emotion_label}, mode={self.intervention_mode})>"
