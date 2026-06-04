"""Tests for the SER inference engine — dummy model predictions and ensemble behavior."""

import numpy as np
import pytest
from cinematic_mood_weaver.emotion.ser_engine import DummySERModel, DummyDimensionalModel, SEREnsemble
from cinematic_mood_weaver.sensors.audio_capture import AudioChunk


@pytest.fixture
def dummy_audio():
    return AudioChunk(
        samples=np.zeros(48000, dtype=np.float32),  # 3s @ 16kHz
        sample_rate=16000,
        duration_sec=3.0,
    )


class TestDummySERModel:
    def setup_method(self):
        self.model = DummySERModel("test/test-model")

    def test_predict_returns_valid_output(self, dummy_audio):
        output = self.model.predict(dummy_audio)
        assert output.model_id == "test/test-model"
        assert len(output.class_probabilities) == 8  # 8 emotion classes
        assert abs(sum(output.class_probabilities.values()) - 1.0) < 0.01
        assert output.inference_ms > 0

    def test_probabilities_sum_to_one(self, dummy_audio):
        for _ in range(10):
            output = self.model.predict(dummy_audio)
            total = sum(output.class_probabilities.values())
            assert abs(total - 1.0) < 0.01

    def test_all_emotion_labels_present(self, dummy_audio):
        output = self.model.predict(dummy_audio)
        expected = {"angry", "calm", "disgust", "fearful", "happy", "neutral", "sad", "surprised"}
        assert set(output.class_probabilities.keys()) == expected


class TestDummyDimensionalModel:
    def setup_method(self):
        self.model = DummyDimensionalModel("test/dim-model")

    def test_predict_returns_valid_va(self, dummy_audio):
        va = self.model.predict(dummy_audio)
        assert -1.0 <= va.valence <= 1.0
        assert -1.0 <= va.arousal <= 1.0


class TestSEREnsemble:
    def setup_method(self):
        self.ensemble = SEREnsemble(use_dummy=True)

    def test_analyze_returns_ensemble_result(self, dummy_audio):
        result = self.ensemble.analyze(dummy_audio)
        assert result.emotion_label in [
            "happy", "sad", "angry", "neutral", "anxious", "calm", "surprised", "disgust", "fearful"
        ] or hasattr(result.emotion_label, "value")
        assert -1.0 <= result.va.valence <= 1.0
        assert -1.0 <= result.va.arousal <= 1.0
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.model_outputs) == 2  # classifier + ensemble
        assert result.inference_ms > 0
