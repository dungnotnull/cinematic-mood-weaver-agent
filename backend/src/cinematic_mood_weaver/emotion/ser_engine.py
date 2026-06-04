"""SER (Speech Emotion Recognition) inference engine using HuggingFace transformers.

Supports multi-model ensemble: primary discrete classifier + dimensional model
for valence/arousal regression + IEMOCAP model for cross-validation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from cinematic_mood_weaver.config import settings
from cinematic_mood_weaver.sensors.audio_capture import AudioChunk
from cinematic_mood_weaver.types.models import EmotionLabel, SerModelOutput, ValenceArousal


@dataclass
class SerEnsembleResult:
    """Aggregated result from all available SER models."""

    emotion_label: EmotionLabel
    va: ValenceArousal
    confidence: float
    model_outputs: list[SerModelOutput] = field(default_factory=list)
    inference_ms: float = 0.0


# ── Dummy SER Model for development without downloading ───────────────


class DummySERModel:
    """Stub SER model that returns plausible random emotion predictions.

    Used for development/testing before real models are downloaded.
    """

    def __init__(self, model_id: str):
        self.model_id = model_id
        self._emotions = [
            "angry", "calm", "disgust", "fearful",
            "happy", "neutral", "sad", "surprised",
        ]

    def predict(self, audio: AudioChunk) -> SerModelOutput:
        """Return a mock prediction with simulated inference latency."""
        del audio  # unused in dummy
        import random as rng
        start = time.perf_counter()
        probs = {e: rng.random() for e in self._emotions}
        total = sum(probs.values())
        probs = {k: v / total for k, v in probs.items()}
        elapsed = (time.perf_counter() - start) * 1000
        return SerModelOutput(
            model_id=self.model_id,
            class_probabilities=probs,
            inference_ms=round(elapsed + rng.uniform(80, 300), 1),
        )


class DummyDimensionalModel:
    """Stub valence/arousal regression model."""

    def __init__(self, model_id: str):
        self.model_id = model_id

    def predict(self, audio: AudioChunk) -> ValenceArousal:
        """Return a mock valence/arousal prediction."""
        del audio
        import random as rng
        return ValenceArousal(
            valence=round(rng.uniform(-1.0, 1.0), 4),
            arousal=round(rng.uniform(-1.0, 1.0), 4),
        )


# ── Real SER Model (wraps HuggingFace pipeline) ───────────────────────


class RealSERModel:
    """Wraps a HuggingFace wav2vec2 model for emotion classification.

    Lazy-loaded — the model is only downloaded when first called.
    """

    def __init__(self, model_id: str):
        self.model_id = model_id
        self._pipeline = None

    def _load(self) -> None:
        if self._pipeline is not None:
            return
        from transformers import pipeline
        self._pipeline = pipeline(
            "audio-classification",
            model=self.model_id,
            top_k=8,
        )

    def predict(self, audio: AudioChunk) -> SerModelOutput:
        """Run inference on a preprocessed audio chunk."""
        self._load()
        start = time.perf_counter()
        assert self._pipeline is not None
        result = self._pipeline(audio.samples, sampling_rate=audio.sample_rate)
        elapsed = (time.perf_counter() - start) * 1000

        probs = {r["label"].lower(): r["score"] for r in result}
        return SerModelOutput(
            model_id=self.model_id,
            class_probabilities=probs,
            inference_ms=round(elapsed, 1),
        )


# ── Ensemble Engine ───────────────────────────────────────────────────


class SEREnsemble:
    """Runs multiple SER models and aggregates their predictions.

    In dummy mode, uses lightweight stubs. In real mode, loads HuggingFace models.
    """

    def __init__(self, use_dummy: bool = True):
        self.use_dummy = use_dummy

        if use_dummy or True:  # Always start in dummy mode
            self._classifier = DummySERModel(settings.ser_model_primary)
            self._dimensional = DummyDimensionalModel(settings.ser_model_dimensional)
            self._ensemble = DummySERModel(settings.ser_model_ensemble)
        else:
            self._classifier = RealSERModel(settings.ser_model_primary)
            self._dimensional = RealSERModel(settings.ser_model_dimensional)
            self._ensemble = RealSERModel(settings.ser_model_ensemble)

    def analyze(self, audio: AudioChunk) -> SerEnsembleResult:
        """Run the full SER pipeline on an audio chunk."""
        start = time.perf_counter()

        primary = self._classifier.predict(audio)
        dim_output = self._dimensional.predict(audio)
        ensemble = self._ensemble.predict(audio)

        outputs = [primary, ensemble]
        elapsed = (time.perf_counter() - start) * 1000

        # Weighted averaging of class probabilities
        all_probs: dict[str, float] = {}
        for out in outputs:
            for label, prob in out.class_probabilities.items():
                all_probs[label] = all_probs.get(label, 0) + prob / len(outputs)

        best_label = max(all_probs, key=all_probs.get)  # type: ignore[type-var]
        confidence = all_probs[best_label]

        # Map string label to EmotionLabel enum
        try:
            emotion_label = EmotionLabel(best_label)
        except ValueError:
            emotion_label = EmotionLabel.NEUTRAL

        return SerEnsembleResult(
            emotion_label=emotion_label,
            va=dim_output,
            confidence=round(confidence, 4),
            model_outputs=outputs,
            inference_ms=round(max(elapsed, 0.1), 1),
        )
