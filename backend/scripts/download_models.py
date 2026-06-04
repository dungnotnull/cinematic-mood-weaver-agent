"""Phase 0b — SER model downloader for local inference benchmarking.

Downloads the 3 HuggingFace SER models into a local cache directory.
Supports --dry-run, --resume, and per-model selection.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ── Model Registry ───────────────────────────────────────────────────


@dataclass
class SerModel:
    id: str
    display_name: str
    purpose: str
    size_mb: int  # approximate download size


SER_MODELS: list[SerModel] = [
    SerModel(
        "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
        "ehcalabres",
        "Primary 8-class SER (RAVDESS, TESS)",
        1250,
    ),
    SerModel(
        "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim",
        "audeering",
        "Dimensional valence/arousal regression (MSP-Podcast)",
        1250,
    ),
    SerModel(
        "speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
        "speechbrain",
        "IEMOCAP-trained 4-class SER ensemble cross-validation",
        1250,
    ),
]


def get_cache_dir() -> Path:
    """Return the HuggingFace cache directory for model storage."""
    from huggingface_hub import scan_cache_dir
    try:
        cache_info = scan_cache_dir()
        return Path(cache_info.repo_path_or_local)
    except Exception:
        # Fallback to default path
        return Path.home() / ".cache" / "huggingface" / "hub"


def check_model_cached(model_id: str, dry_run: bool) -> bool:
    """Check if a model is already cached locally."""
    if dry_run:
        return False
    try:
        from huggingface_hub import scan_cache_dir
        cache_info = scan_cache_dir()
        for repo in cache_info.repos:
            if model_id in repo.repo_id:
                return True
        return False
    except Exception:
        return False


def download_model(model: SerModel, dry_run: bool, resume: bool = False) -> bool:
    """Download a single SER model from HuggingFace.

    In --dry-run mode, only reports what would be downloaded.
    With --resume, skips if already fully cached.
    """
    print(f"\n  [{model.display_name}] {model.purpose}")
    print(f"    Model ID: {model.id}")
    print(f"    Approx size: {model.size_mb} MB")

    if dry_run:
        already = "(already cached)" if check_model_cached(model.id, dry_run=False) else ""
        print(f"    Status: ⊘ Dry run — would download{already}")
        return True

    # Check if already cached
    if resume:
        try:
            from huggingface_hub import try_to_load_from_cache

            # Try loading a key file to see if model exists
            result = try_to_load_from_cache(
                repo_id=model.id,
                filename="config.json",
            )
            if result is not None and not isinstance(result, str):
                print(f"    Status: ✓ Already cached locally")
                return True
        except Exception:
            pass

    print(f"    Status: ▼ Downloading...", end="", flush=True)

    try:
        from huggingface_hub import snapshot_download

        start = time.perf_counter()
        local_path = snapshot_download(
            repo_id=model.id,
            ignore_patterns=["*.h5", "*.ot", "*.msgpack"],
            local_files_only=False,
        )
        elapsed = time.perf_counter() - start

        size = sum(f.stat().st_size for f in Path(local_path).rglob("*") if f.is_file())
        size_mb = size / (1024 * 1024)
        print(f"\r    Status: ✓ Downloaded {size_mb:.0f} MB in {elapsed:.1f}s")
        print(f"    Path: {local_path}")
        return True

    except Exception as e:
        print(f"\r    Status: ✗ Failed — {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Download SER models for Cinematic Mood Weaver")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded without downloading")
    parser.add_argument("--resume", action="store_true", help="Skip already-cached models")
    parser.add_argument("--model", type=str, default="", help="Download only a specific model (partial name match)")
    args = parser.parse_args()

    print("=" * 56)
    print("  Cinematic Mood Weaver — SER Model Download")
    print("=" * 56)

    if not args.dry_run:
        # Ensure huggingface_hub is available
        try:
            import huggingface_hub  # noqa: F401
        except ImportError:
            print("\n  ✗ huggingface_hub not installed. Run `pip install huggingface_hub` first.\n")
            return 1

    models = SER_MODELS
    if args.model:
        models = [m for m in models if args.model.lower() in m.id.lower() or args.model.lower() in m.display_name.lower()]
        if not models:
            print(f"\n  ✗ No models matched '{args.model}'")
            print(f"    Available: {', '.join(m.display_name for m in SER_MODELS)}")
            return 1

    cache_dir = get_cache_dir() if not args.dry_run else Path("?")
    if not args.dry_run:
        print(f"\n  Cache: {cache_dir}\n")
    else:
        print(f"\n  (dry run — no actual downloads)\n")

    results: list[bool] = []
    for model in models:
        results.append(download_model(model, dry_run=args.dry_run, resume=args.resume))

    success = all(results)
    print(f"\n  {'✓ All models ready' if success else '✗ Some downloads failed'}")
    print()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
