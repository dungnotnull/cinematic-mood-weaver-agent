"""SQLAlchemy database engine, session factory, and table creation."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from cinematic_mood_weaver.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_engine = None
_SessionLocal = None


def get_engine():
    """Lazy-create and return the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        db_dir = Path(settings.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{settings.db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return _engine


def get_session() -> sessionmaker:
    """Return the configured Session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


def init_db():
    """Create all tables defined in models that inherit from Base."""
    from .models import (  # noqa: F401  — register models
        MashupLog,
        MoodHistory,
        UserPreference,
    )

    Base.metadata.create_all(bind=get_engine())


def create_session():
    """Yield a new SQLAlchemy session context manager style."""
    session_factory = get_session()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
