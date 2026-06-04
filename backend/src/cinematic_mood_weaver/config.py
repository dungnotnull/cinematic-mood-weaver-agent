"""Application configuration via pydantic-settings + .env file."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration, loaded from .env or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Paths ─────────────────────────────────────────────────────────
    db_path: str = str(Path.home() / ".cinematic-mood-weaver" / "data.db")
    app_data_dir: str = str(Path.home() / ".cinematic-mood-weaver")

    # ── LLM API Keys ──────────────────────────────────────────────────
    claude_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"

    # ── External Service API Keys ──────────────────────────────────────
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    tmdb_api_key: Optional[str] = None

    # ── Smart Home ────────────────────────────────────────────────────
    hue_bridge_ip: Optional[str] = None
    home_assistant_url: Optional[str] = None
    home_assistant_token: Optional[str] = None

    # ── SER Models ────────────────────────────────────────────────────
    ser_model_primary: str = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
    ser_model_dimensional: str = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"
    ser_model_ensemble: str = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP"

    # ── Pipeline Defaults ─────────────────────────────────────────────
    audio_sample_rate: int = 16000
    audio_window_seconds: float = 3.0
    ser_poll_interval_seconds: int = 300
    confidence_threshold: float = 0.6
    enable_lighting: bool = True
    enable_biometrics: bool = False
    enable_aromatherapy: bool = False
    preferred_llm_backend: str = "claude"  # "claude" | "openai" | "ollama" | "template"

    # ── AES Encryption ────────────────────────────────────────────────
    encryption_key: Optional[str] = None

    @property
    def db_dir(self) -> Path:
        return Path(self.db_path).parent


settings = Settings()
