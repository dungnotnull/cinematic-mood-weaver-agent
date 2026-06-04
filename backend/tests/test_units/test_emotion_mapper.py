"""Tests for the emotion mapper — valence/arousal mapping and label classification."""

import pytest
from cinematic_mood_weaver.emotion.emotion_mapper import (
    EmotionMapper,
    BiometricFusion,
    probability_vector_to_va,
    va_to_nearest_label,
)
from cinematic_mood_weaver.types.models import EmotionLabel, ValenceArousal


class TestProbabilityVectorToVA:
    def test_happy_vector(self):
        probs = {"happy": 0.8, "neutral": 0.1, "sad": 0.1}
        va = probability_vector_to_va(probs)
        assert va.valence > 0
        assert va.arousal > 0

    def test_sad_vector(self):
        probs = {"sad": 0.8, "neutral": 0.1, "angry": 0.1}
        va = probability_vector_to_va(probs)
        assert va.valence < 0
        assert va.arousal < 0

    def test_neutral_vector(self):
        probs = {"neutral": 1.0}
        va = probability_vector_to_va(probs)
        assert abs(va.valence) < 0.1
        assert abs(va.arousal) < 0.1

    def test_empty_vector_returns_zero(self):
        va = probability_vector_to_va({})
        assert va.valence == 0.0
        assert va.arousal == 0.0

    def test_clipped_range(self):
        probs = {"happy": 100, "sad": 100}
        va = probability_vector_to_va(probs)
        assert -1.0 <= va.valence <= 1.0
        assert -1.0 <= va.arousal <= 1.0


class TestVAToNearestLabel:
    def test_happy_region(self):
        label, sim = va_to_nearest_label(ValenceArousal(valence=0.8, arousal=0.7))
        assert label == EmotionLabel.HAPPY
        assert sim > 0.9

    def test_sad_region(self):
        label, sim = va_to_nearest_label(ValenceArousal(valence=-0.8, arousal=-0.6))
        assert label == EmotionLabel.SAD
        assert sim > 0.9

    def test_neutral_origin(self):
        label, sim = va_to_nearest_label(ValenceArousal(valence=0.0, arousal=0.0))
        assert label == EmotionLabel.NEUTRAL
        assert sim >= 0.0


class TestEmotionMapper:
    def setup_method(self):
        self.mapper = EmotionMapper()

    def test_map_from_ser_probabilities(self):
        probs = {"happy": 0.7, "calm": 0.2, "neutral": 0.1}
        state = self.mapper.map_from_ser_probabilities(probs, confidence=0.8)
        assert state.label in EmotionLabel
        assert 0.0 <= state.confidence <= 1.0
        assert state.source == "ser"
        assert -1.0 <= state.va.valence <= 1.0
        assert -1.0 <= state.va.arousal <= 1.0

    def test_map_from_va(self):
        state = self.mapper.map_from_va(ValenceArousal(valence=0.0, arousal=0.0), confidence=0.9)
        assert state.label == EmotionLabel.NEUTRAL
        assert state.confidence == 0.9


class TestBiometricFusion:
    def setup_method(self):
        self.fusion = BiometricFusion()

    def test_normalize_hrv_low_stress(self):
        score = self.fusion.normalize_hrv(rmssd=70.0)
        assert score == 0.0  # High HRV = low stress

    def test_normalize_hrv_high_stress(self):
        score = self.fusion.normalize_hrv(rmssd=20.0)
        assert score == 1.0  # Low HRV = high stress

    def test_normalize_hrv_mid(self):
        score = self.fusion.normalize_hrv(rmssd=42.5)
        assert 0.0 < score < 1.0

    def test_normalize_hr_resting(self):
        score = self.fusion.normalize_heart_rate(60.0)
        assert score == 0.0

    def test_normalize_hr_elevated(self):
        score = self.fusion.normalize_heart_rate(90.0)
        assert 0.4 < score < 0.6

    def test_normalize_hr_high(self):
        score = self.fusion.normalize_heart_rate(120.0)
        assert score == 1.0

    def test_fusion_adjusts_arousal(self):
        from cinematic_mood_weaver.types.models import EmotionState
        ser = EmotionState(va=ValenceArousal(valence=0.0, arousal=0.5), label=EmotionLabel.ANXIOUS, confidence=0.7)
        fused = self.fusion.fuse(ser, hrv_rmssd=25.0, heart_rate_bpm=95.0, ser_weight=0.7)
        assert fused.source == "fusion"
        assert fused.confidence >= ser.confidence  # Fusion should be at least as confident
