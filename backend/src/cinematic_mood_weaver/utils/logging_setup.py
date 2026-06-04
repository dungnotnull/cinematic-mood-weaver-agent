"""Logging configuration for the Cinematic Mood Weaver."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from cinematic_mood_weaver.config import settings


def setup_logging(level: str = "INFO") -> None:
    """Configure application-wide logging with file and console output."""
    logger = logging.getLogger("cinematic_mood_weaver")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler
    log_dir = Path(settings.app_data_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "cinematic-mood-weaver.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
