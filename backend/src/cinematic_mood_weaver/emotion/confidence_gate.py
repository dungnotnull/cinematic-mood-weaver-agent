"""Confidence gating — determines when the system should prompt the user
for manual mood confirmation vs. proceeding with automatic inference.

When SER confidence falls below threshold, the system pauses and asks
the user to confirm or correct their detected emotion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from cinematic_mood_weaver.config import settings
from cinematic_mood_weaver.db.service import get_mood_history_since
from cinematic_mood_weaver.types.models import EmotionState


@dataclass
class ConfidenceVerdict:
    """Result of confidence gating evaluation."""

    needs_confirmation: bool
    reason: str = ""
    current_confidence: float = 0.0
    threshold: float = 0.6
    last_prompted: Optional[datetime] = None


class ConfidenceGate:
    """Evaluates whether the current emotion inference is trustworthy enough
    to act on, or if the user should be asked to confirm.

    Triggers confirmation when:
    - Confidence is below threshold (< 0.6)
    - Recent volatility is high (mood swinging rapidly)
    - Multiple sources disagree (SER vs biometric conflict)
    """

    def __init__(self, threshold: float = 0.0):
        self.threshold = threshold or settings.confidence_threshold
        self._last_prompt_time: Optional[datetime] = None
        self._cooldown_seconds = 120  # Don't re-prompt more than once per 2 min

    def evaluate(self, emotion: EmotionState) -> ConfidenceVerdict:
        """Evaluate whether user confirmation is needed."""
        # Check cooldown — don't spam the user
        if self._last_prompt_time:
            elapsed = (datetime.now() - self._last_prompt_time).total_seconds()
            if elapsed < self._cooldown_seconds:
                return ConfidenceVerdict(
                    needs_confirmation=False,
                    reason="cooldown",
                    current_confidence=emotion.confidence,
                    threshold=self.threshold,
                    last_prompted=self._last_prompt_time,
                )

        # Low confidence trigger
        if emotion.confidence < self.threshold:
            self._last_prompt_time = datetime.now()
            return ConfidenceVerdict(
                needs_confirmation=True,
                reason=f"low_confidence ({emotion.confidence:.2f} < {self.threshold})",
                current_confidence=emotion.confidence,
                threshold=self.threshold,
                last_prompted=self._last_prompt_time,
            )

        # High volatility trigger
        recent = get_mood_history_since(hours=0.5)
        if len(recent) >= 3:
            valences = [e.valence for e in recent[-3:]]
            volatility = max(valences) - min(valences)
            if volatility > 0.8:
                self._last_prompt_time = datetime.now()
                return ConfidenceVerdict(
                    needs_confirmation=True,
                    reason=f"high_volatility ({volatility:.2f})",
                    current_confidence=emotion.confidence,
                    threshold=self.threshold,
                    last_prompted=self._last_prompt_time,
                )

        return ConfidenceVerdict(
            needs_confirmation=False,
            reason="sufficient_confidence",
            current_confidence=emotion.confidence,
            threshold=self.threshold,
            last_prompted=self._last_prompt_time,
        )

    def reset(self) -> None:
        """Reset the prompt cooldown."""
        self._last_prompt_time = None
