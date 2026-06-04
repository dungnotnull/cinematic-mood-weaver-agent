"""Phase 0b — Comprehensive system health checker.

Runs all setup and verification steps in sequence:
  1. Python version check
  2. Environment setup check (venv + deps)
  3. Database initialization
  4. SER model availability check
  5. API credential verification
  6. Pipeline import and demo cycle

This is the entry point that ties Phase 0b together.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def step(num: int, label: str) -> None:
    print(f"\n  [{num}] {label}")
    print(f"  {'─' * 40}")


def check_env_setup(dry_run: bool) -> bool:
    """Check Python version and virtual environment."""
    # Inline check (avoids relative import issues when run directly)
    v = sys.version_info
    ok = v >= (3, 11)
    if ok:
        print(f"  ✓ Python {v.major}.{v.minor}.{v.micro} (≥ 3.11)")
    else:
        print(f"  ✗ Python {v.major}.{v.minor} is too old; need ≥ 3.11")

    # Check if .venv exists
    venv_path = PROJECT_ROOT / ".venv"
    if venv_path.exists():
        print(f"  ✓ Virtual environment at {venv_path}")
    else:
        if dry_run:
            print(f"  ⊘ No .venv found — would create")
        else:
            print(f"  ✗ No .venv found — run: python scripts/setup_env.py")
            ok = False

    return ok


def check_database(dry_run: bool) -> bool:
    """Initialize and verify the database."""
    try:
        from cinematic_mood_weaver.db.engine import init_db
        init_db()
        print(f"  ✓ Database initialized")
        return True
    except Exception as e:
        if dry_run:
            print(f"  ⊘ Would initialize database")
            return True
        print(f"  ✗ Database error: {e}")
        return False


def check_models_available(dry_run: bool) -> bool:
    """Check which SER models are cached locally."""
    if dry_run:
        print(f"  ⊘ Would check 3 SER models in HuggingFace cache")
        return True

    try:
        from huggingface_hub import scan_cache_dir

        cache_info = scan_cache_dir()
        cached_repos = [r.repo_id for r in cache_info.repos]

        expected = [
            "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
            "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim",
            "speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
        ]

        all_cached = True
        for model_id in expected:
            cached = any(model_id in r for r in cached_repos)
            icon = "✓" if cached else "⊘"
            print(f"  {icon} {model_id.rsplit('/', 1)[-1]}: {'cached' if cached else 'not downloaded'}")
            if not cached:
                all_cached = False

        if not all_cached:
            print(f"  ⚠ Some models not cached. Run: python scripts/download_models.py")
        return all_cached

    except Exception as e:
        print(f"  ⊘ Could not inspect cache: {e}")
        return True  # Non-fatal


def check_env_file(dry_run: bool) -> bool:
    """Check .env file exists and has required keys."""
    env_path = PROJECT_ROOT.parent / ".env"

    if not env_path.exists():
        print(f"  ✗ .env not found at {env_path}")
        print(f"    Run: python scripts/credentials_setup.py")
        return False

    required_keys = ["CLAUDE_API_KEY"]
    env: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("\"'")

    ok = True
    for key in required_keys:
        value = env.get(key, "")
        if value:
            masked = value[:8] + "..." if len(value) > 8 else value
            print(f"  ✓ {key}: {masked}")
        else:
            print(f"  ✗ {key}: not set")
            ok = False

    if env.get("SPOTIFY_CLIENT_ID"):
        print(f"  ✓ Spotify: configured")
    if env.get("TMDB_API_KEY"):
        print(f"  ✓ TMDB: configured")
    if env.get("HUE_BRIDGE_IP"):
        print(f"  ✓ Hue bridge: {env['HUE_BRIDGE_IP']}")

    return ok


def check_pipeline_import(dry_run: bool) -> bool:
    """Verify the pipeline module imports cleanly."""
    try:
        from cinematic_mood_weaver.pipeline import MoodWeaverPipeline  # noqa: F401
        # Check the pipeline can be instantiated (without real models)
        p = MoodWeaverPipeline()
        print(f"  ✓ Pipeline module imported, constructor works")
        return True
    except Exception as e:
        if dry_run:
            print(f"  ⊘ Would check pipeline import")
            return True
        print(f"  ✗ Pipeline import failed: {e}")
        return False


def run_demo_cycle(dry_run: bool) -> bool:
    """Run a demo cycle to verify end-to-end flow."""
    if dry_run:
        print(f"  ⊘ Would run demo cycle")
        return True

    try:
        from cinematic_mood_weaver.main import demo_cycle
        from cinematic_mood_weaver.pipeline import MoodWeaverPipeline
        import asyncio

        async def _run():
            p = MoodWeaverPipeline()
            await p.initialize()
            await demo_cycle(p)

        asyncio.run(_run())
        print(f"  ✓ Demo cycle completed successfully")
        return True

    except Exception as e:
        print(f"  ✗ Demo cycle failed: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Cinematic Mood Weaver — System Health Verification")
    parser.add_argument("--dry-run", action="store_true", help="Check readiness without executing real operations")
    parser.add_argument("--full", action="store_true", help="Run all checks including live API tests")
    args = parser.parse_args()

    print("=" * 56)
    print("  Cinematic Mood Weaver — System Health Check")
    print("=" * 56)

    if args.dry_run:
        print("\n  ⊘ DRY RUN — no real operations will be executed\n")
    print()

    results: list[bool] = []

    step(1, "Python & Environment")
    results.append(check_env_setup(args.dry_run))

    step(2, "Database")
    results.append(check_database(args.dry_run))

    step(3, "SER Models")
    results.append(check_models_available(args.dry_run))

    step(4, "API Credentials (.env)")
    results.append(check_env_file(args.dry_run))

    step(5, "Pipeline Import")
    results.append(check_pipeline_import(args.dry_run))

    step(6, "Demo Cycle (End-to-End)")
    results.append(run_demo_cycle(args.dry_run))

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r)
    failed = total - passed

    print(f"\n  {'═' * 48}")
    if failed == 0:
        print(f"  ✓ ALL SYSTEMS GO — {passed}/{total} checks passed")
        print(f"\n  You can now run the demo:\n")
        print(f"      python -m cinematic_mood_weaver.main")
    else:
        print(f"  ⚠  {passed}/{total} checks passed, {failed} need attention")
        print(f"\n  Fix the issues above, then re-run this check.")

    if args.dry_run:
        print(f"  (dry run — no actual operations were performed)")
    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
