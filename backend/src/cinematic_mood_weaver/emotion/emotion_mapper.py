"""Emotion mapper — converts SER probability vectors and biometric signals into
a unified (valence, arousal) → emotion label with confidence scoring.

Implements Russell's circumplex model mapping and biometric fusion ensemble.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from cinematic_mood_weaver.types.models import EmotionLabel, EmotionState, ValenceArousal


# ── Valence/Arousal coordinates for canonical emotion labels ──────────
# Based on Russell's circumplex model of affect (1980).

CANONICAL_VA: dict[EmotionLabel, ValenceArousal] = {
    EmotionLabel.HAPPY: ValenceArousal(valence=0.81, arousal=0.75),
    EmotionLabel.CALM: ValenceArousal(valence=0.70, arousal=-0.70),
    EmotionLabel.NEUTRAL: ValenceArousal(valence=0.0, arousal=0.0),
    EmotionLabel.SAD: ValenceArousal(valence=-0.80, arousal=-0.60),
    EmotionLabel.ANGRY: ValenceArousal(valence=-0.70, arousal=0.80),
    EmotionLabel.ANXIOUS: ValenceArousal(valence=-0.40, arousal=0.70),
    EmotionLabel.SURPRISED: ValenceArousal(valence=0.40, arousal=0.90),
    EmotionLabel.DISGUST: ValenceArousal(valence=-0.60, arousal=0.30),
    EmotionLabel.FEARFUL: ValenceArousal(valence=-0.70, arousal=0.50),
}


def probability_vector_to_va(probs: dict[str, float]) -> ValenceArousal:
    """Convert a probability vector over emotion labels to weighted (v, a) coordinates."""
    valence = 0.0
    arousal = 0.0
    total_weight = 0.0

    for label_str, prob in probs.items():
        try:
            label = EmotionLabel(label_str)
        except ValueError:
            continue
        canonical = CANONICAL_VA.get(label)
        if canonical:
            valence += canonical.valence * prob
            arousal += canonical.arousal * prob
            total_weight += prob

    if total_weight > 0:
        valence /= total_weight
        arousal /= total_weight

    return ValenceArousal(
        valence=round(float(np.clip(valence, -1.0, 1.0)), 4),
        arousal=round(float(np.clip(arousal, -1.0, 1.0)), 4),
    )


def va_to_nearest_label(va: ValenceArousal) -> tuple[EmotionLabel, float]:
    """Find the canonical emotion label closest to the given (v, a) coordinates.

    Returns (label, cosine_similarity_score).
    At the origin (0,0) the result is NEUTRAL by definition.
    """
    norm_v = np.sqrt(va.valence**2 + va.arousal**2)
    if norm_v < 0.001:
        return EmotionLabel.NEUTRAL, 1.0

    best_label = EmotionLabel.NEUTRAL
    best_sim = -1.0

    for label, canonical in CANONICAL_VA.items():
        norm_c = np.sqrt(canonical.valence**2 + canonical.arousal**2) or 1.0
        sim = (va.valence * canonical.valence + va.arousal * canonical.arousal) / (norm_v * norm_c)
        if sim > best_sim:
            best_sim = sim
            best_label = label

    return best_label, round(float(best_sim), 4)


class EmotionMapper:
    """Transforms raw SER/biometric signals into EmotionState objects."""

    def map_from_ser_probabilities(
        self, probs: dict[str, float], confidence: float, source: str = "ser"
    ) -> EmotionState:
        """Map a SER probability vector to an EmotionState."""
        va = probability_vector_to_va(probs)
        label, _ = va_to_nearest_label(va)
        return EmotionState(va=va, label=label, confidence=confidence, source=source)

    def map_from_va(
        self, va: ValenceArousal, confidence: float, source: str = "ser"
    ) -> EmotionState:
        """Map known (valance, arousal) coordinates to an EmotionState."""
        label, _ = va_to_nearest_label(va)
        return EmotionState(va=va, label=label, confidence=confidence, source=source)


class BiometricFusion:
    """Fuses SER output with biometric data for improved accuracy.

    When wearable data (HRV, heart rate) is available, it is normalized and
    combined with the SER result using a weighted ensemble.
    """

    @staticmethod
    def normalize_hrv(rmssd: float) -> float:
        """Normalize HRV RMSSD to a 0-1 stress scale where 1 = high stress.

        Typical RMSSD range: 20-80ms.
        - Low RMSSD (<25) → high stress → high score
        - High RMSSD (>65) → low stress → low score
        """
        if rmssd >= 65:
            return 0.0
        if rmssd <= 20:
            return 1.0
        return round(1.0 - (rmssd - 20) / 45, 4)

    @staticmethod
    def normalize_heart_rate(bpm: float) -> float:
        """Normalize heart rate to a 0-1 arousal scale.

        Resting: 60-80 BPM → low arousal (0.0-0.3)
        Elevated: 80-100 → moderate arousal (0.3-0.6)
        High: >100 → high arousal (0.6-1.0)
        """
        if bpm <= 60:
            return 0.0
        if bpm >= 120:
            return 1.0
        return round((bpm - 60) / 60, 4)

    def fuse(
        self,
        ser_emotion: EmotionState,
        hrv_rmssd: float,
        heart_rate_bpm: float,
        ser_weight: float = 0.7,
    ) -> EmotionState:
        """Weighted fusion of SER and biometric signals.

        The biometric signal provides an independent stress/arousal estimate
        that adjusts the SER's arousal dimension.
        """
        stress = self.normalize_hrv(hrv_rmssd)
        bpm_arousal = self.normalize_heart_rate(heart_rate_bpm)
        bio_arousal = (stress + bpm_arousal) / 2.0

        # Blend arousal: SER arousal weighted against biometric arousal
        blended_arousal = (
            ser_emotion.va.arousal * ser_weight + (bio_arousal * 2 - 1) * (1 - ser_weight)
        )
        blended_arousal = float(np.clip(blended_arousal, -1.0, 1.0))

        fused_va = ValenceArousal(valence=ser_emotion.va.valence, arousal=round(blended_arousal, 4))
        label, _ = va_to_nearest_label(fused_va)

        # Fusion confidence is slightly higher than SER alone
        fused_confidence = min(1.0, ser_emotion.confidence + 0.05)

        return EmotionState(va=fused_va, label=label, confidence=round(fused_confidence, 4), source="fusion")
