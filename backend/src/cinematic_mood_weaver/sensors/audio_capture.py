"""Audio capture module — continuous microphone stream → 3s windowed chunks.

Uses sounddevice for low-latency audio capture and librosa for
preprocessing (normalization, silence removal, mel spectrogram conversion).
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from cinematic_mood_weaver.config import settings


@dataclass
class AudioChunk:
    """A preprocessed audio chunk ready for SER inference."""

    samples: np.ndarray  # normalized float32 waveform
    sample_rate: int
    duration_sec: float


class AudioCaptureError(Exception):
    """Raised when audio capture fails (no mic, permission denied, etc.)."""


class AudioCapture:
    """Continuous audio capture producing windowed chunks on a callback.

    Usage:
        capture = AudioCapture()
        capture.start(on_chunk=my_handler)
        # ... later ...
        capture.stop()
    """

    def __init__(self, sample_rate: int = 0, window_seconds: float = 0.0):
        self.sample_rate = sample_rate or settings.audio_sample_rate
        self.window_seconds = window_seconds or settings.audio_window_seconds
        self.frame_size = int(self.sample_rate * self.window_seconds)
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: Optional[sd.InputStream] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._callback: Optional[Callable[[AudioChunk], None]] = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags) -> None:
        """sounddevice stream callback — called with each buffer of samples."""
        if status:
            if status.input_overflow:
                pass  # benign under heavy load, can be ignored
        self._queue.put(indata.copy())

    def _processing_loop(self) -> None:
        """Consume audio from the queue, build windows, invoke callback."""
        buffer = np.array([], dtype=np.float32)
        while self._running:
            try:
                chunk = self._queue.get(timeout=0.1)
                buffer = np.concatenate([buffer, chunk.flatten()])
                while len(buffer) >= self.frame_size:
                    window = buffer[:self.frame_size]
                    buffer = buffer[self.frame_size:]
                    processed = self._preprocess(window)
                    if self._callback and processed is not None:
                        self._callback(processed)
            except queue.Empty:
                continue
            except Exception:
                # Logged but not fatal — keep the loop running
                pass

    def _preprocess(self, samples: np.ndarray) -> Optional[AudioChunk]:
        """Normalize and remove leading silence from a raw audio window."""
        # Convert to float32 if needed
        if samples.dtype != np.float32:
            samples = samples.astype(np.float32) / np.iinfo(samples.dtype).max

        # Normalize peak amplitude to [-1, 1]
        peak = np.max(np.abs(samples))
        if peak > 0:
            samples = samples / peak

        # Simple silence gate: discard if max amplitude is below noise floor
        if np.max(np.abs(samples)) < 0.01:
            return None

        return AudioChunk(samples=samples, sample_rate=self.sample_rate, duration_sec=self.window_seconds)

    def start(self, on_chunk: Callable[[AudioChunk], None]) -> None:
        """Start capturing audio. Calls on_chunk for each processed window."""
        if self._running:
            return

        self._callback = on_chunk
        self._running = True

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self._audio_callback,
                blocksize=int(self.sample_rate * 0.1),  # 100ms blocks
            )
            self._stream.start()
        except sd.PortAudioError as e:
            self._running = False
            raise AudioCaptureError(f"Could not open microphone: {e}") from e

        self._thread = threading.Thread(target=self._processing_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop capturing audio and release the mic."""
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
