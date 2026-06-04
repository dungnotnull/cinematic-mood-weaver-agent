"""Phase 0b — SER model inference speed benchmark.

Measures inference latency (CPU and CUDA) for each downloaded SER model
using a synthetic test audio sample. Generates a performance report.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np


SAMPLE_RATE = 16000
DURATION_SEC = 3.0
NUM_WARMUP = 3
NUM_ITERATIONS = 20


def generate_test_signal() -> np.ndarray:
    """Generate a synthetic 3-second speech-like signal for benchmarking."""
    t = np.linspace(0, DURATION_SEC, int(SAMPLE_RATE * DURATION_SEC), endpoint=False)
    # Mix of formant-like frequencies + noise to simulate speech
    signal = (
        0.3 * np.sin(2 * np.pi * 200 * t)
        + 0.2 * np.sin(2 * np.pi * 800 * t)
        + 0.1 * np.sin(2 * np.pi * 2400 * t)
        + 0.1 * np.random.randn(len(t))
    )
    return signal.astype(np.float32)


def benchmark_on_device(
    model_id: str,
    device: str,
    dry_run: bool,
) -> Optional[dict]:
    """Benchmark a single model on a given device. Returns timing stats."""
    if dry_run:
        return {
            "model": model_id,
            "device": device,
            "mean_ms": 0.0,
            "std_ms": 0.0,
            "min_ms": 0.0,
            "max_ms": 0.0,
            "status": "dry_run",
        }

    try:
        from transformers import pipeline

        signal = generate_test_signal()
        pipe = pipeline(
            "audio-classification",
            model=model_id,
            device=device if device == "cpu" else 0,
        )

        # Warmup
        for _ in range(NUM_WARMUP):
            pipe(signal, sampling_rate=SAMPLE_RATE)

        # Timed iterations
        latencies: list[float] = []
        for _ in range(NUM_ITERATIONS):
            start = time.perf_counter()
            pipe(signal, sampling_rate=SAMPLE_RATE)
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

        return {
            "model": model_id.rsplit("/", 1)[-1],
            "device": device,
            "mean_ms": round(float(np.mean(latencies)), 1),
            "std_ms": round(float(np.std(latencies)), 1),
            "min_ms": round(float(np.min(latencies)), 1),
            "max_ms": round(float(np.max(latencies)), 1),
            "status": "ok",
        }

    except Exception as e:
        return {
            "model": model_id.rsplit("/", 1)[-1],
            "device": device,
            "error": str(e),
            "status": "failed",
        }


def print_report(results: list[dict]) -> None:
    """Print a formatted benchmark report."""
    print()
    print(f"  {'Model':<30} {'Device':<8} {'Mean':>8} {'Std':>8} {'Min':>8} {'Max':>8}  Status")
    print(f"  {'─' * 30} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8}  ──────")

    for r in results:
        if r["status"] == "dry_run":
            print(f"  {r['model']:<30} {r['device']:<8} {'—':>8} {'—':>8} {'—':>8} {'—':>8}  ⊘ dry run")
        elif r["status"] == "failed":
            err = r.get("error", "unknown")[:40]
            print(f"  {r['model']:<30} {r['device']:<8} {'':>8} {'':>8} {'':>8} {'':>8}  ✗ {err}")
        else:
            print(
                f"  {r['model']:<30} {r['device']:<8} "
                f"{r['mean_ms']:>6.1f}ms {r['std_ms']:>6.1f}ms "
                f"{r['min_ms']:>6.1f}ms {r['max_ms']:>6.1f}ms  ✓"
            )
    print()


def detect_cuda() -> bool:
    """Check if CUDA is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark SER model inference speed")
    parser.add_argument("--dry-run", action="store_true", help="Preview benchmark without running models")
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "cuda", "all"],
                        help="Target device for inference")
    parser.add_argument("--model", type=str, default="", help="Benchmark only a specific model (partial name match)")
    args = parser.parse_args()

    print("=" * 56)
    print("  Cinematic Mood Weaver — SER Model Benchmark")
    print("=" * 56)

    if not args.dry_run:
        try:
            import torch  # noqa: F401
        except ImportError:
            print("\n  ✗ PyTorch not installed. Run `pip install torch` first.\n")
            return 1

    # Determine which models to benchmark
    ser_model_ids = [
        "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
        "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim",
        "speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
    ]

    if args.model:
        ser_model_ids = [m for m in ser_model_ids if args.model.lower() in m.lower()]
        if not ser_model_ids:
            print(f"\n  ✗ No models matched '{args.model}'")
            return 1

    # Determine devices
    devices = [args.device]
    if args.device == "all":
        devices = ["cpu"]
        if detect_cuda():
            devices.append("cuda")

    cuda_available = detect_cuda() if not args.dry_run else False
    print(f"\n  Test signal: {DURATION_SEC}s @ {SAMPLE_RATE}Hz")
    print(f"  Iterations: {NUM_WARMUP} warmup + {NUM_ITERATIONS} measured")
    print(f"  Devices: {', '.join(devices)}")
    if not args.dry_run and "cuda" in devices and not cuda_available:
        print(f"  ⚠ CUDA requested but not available — CPU fallback")

    print()
    results: list[dict] = []
    for model_id in ser_model_ids:
        for device in devices:
            if device == "cuda" and not cuda_available:
                continue
            short = model_id.rsplit("/", 1)[-1]
            status = "⊘" if args.dry_run else "▶"
            print(f"  {status} Benchmarking {short} on {device}...")
            result = benchmark_on_device(model_id, device, args.dry_run)
            if result:
                results.append(result)

    print_report(results)

    # Check success criteria (Phase 0: < 500ms CPU for 3s clip)
    cpu_results = [r for r in results if r["device"] == "cpu" and r["status"] == "ok"]
    if cpu_results:
        passed = all(r["mean_ms"] < 500 for r in cpu_results)
        print(f"  Success criteria: CPU inference < 500ms → {'✓ PASS' if passed else '✗ FAIL'}")
        if not passed:
            for r in cpu_results:
                if r["mean_ms"] >= 500:
                    print(f"    {r['model']}: {r['mean_ms']}ms (target: <500ms)")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
