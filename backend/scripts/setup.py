"""Phase 0b — Master setup orchestrator.

Runs the full Phase 0b workflow in sequence:
  1. Python environment setup (venv + deps)
  2. API credential configuration wizard
  3. SER model downloads
  4. SER model benchmark
  5. Smoke test all connections
  6. Run demo cycle

Supports --step to run only specific steps, and --dry-run for preview.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


STEPS = {
    "env": {
        "label": "Python environment setup",
        "script": PROJECT_ROOT / "scripts" / "setup_env.py",
        "required": True,
    },
    "credentials": {
        "label": "API credential configuration",
        "script": PROJECT_ROOT / "scripts" / "credentials_setup.py",
        "required": False,
    },
    "models": {
        "label": "SER model downloads",
        "script": PROJECT_ROOT / "scripts" / "download_models.py",
        "required": False,
    },
    "benchmark": {
        "label": "SER model benchmarks",
        "script": PROJECT_ROOT / "scripts" / "benchmark_models.py",
        "required": False,
    },
    "smoke": {
        "label": "Smoke test all connections",
        "script": PROJECT_ROOT / "scripts" / "smoke_test.py",
        "required": False,
    },
    "health": {
        "label": "Full health check + demo cycle",
        "script": PROJECT_ROOT / "scripts" / "verify_health.py",
        "required": False,
    },
}


def run_step(step_key: str, dry_run: bool) -> bool:
    """Run a single setup step or simulate it."""
    step = STEPS[step_key]
    script = step["script"]
    label = step["label"]

    print(f"\n{'=' * 56}")
    print(f"  Step: {label}")
    print(f"{'=' * 56}")

    if not script.exists():
        print(f"  ✗ Script not found: {script}")
        return False

    if dry_run:
        print(f"  ⊘ Would run: {PYTHON} {script} --dry-run")
        return True

    cmd = [PYTHON, str(script)]
    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    ok = result.returncode == 0
    if ok:
        print(f"  ✓ Step completed successfully")
    else:
        print(f"  ✗ Step failed (exit code {result.returncode})")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Cinematic Mood Weaver — Phase 0b Master Setup")
    parser.add_argument("--step", type=str, default="", choices=list(STEPS.keys()) + ["all"],
                        help="Run only a specific step")
    parser.add_argument("--dry-run", action="store_true", help="Preview all steps without executing")
    parser.add_argument("--skip", type=str, default="", help="Comma-separated steps to skip")
    args = parser.parse_args()

    print("=" * 56)
    print("  Cinematic Mood Weaver — Phase 0b Setup")
    print("  Environment Setup + Credentials + Models + Verification")
    print("=" * 56)

    skip_set = set(s.strip() for s in args.skip.split(",") if s.strip())

    if args.step and args.step != "all":
        steps_to_run = [args.step]
    else:
        steps_to_run = list(STEPS.keys())

    steps_to_run = [s for s in steps_to_run if s not in skip_set]

    results: list[tuple[str, bool]] = []
    for step_key in steps_to_run:
        ok = run_step(step_key, args.dry_run)
        results.append((step_key, ok))
        if not ok and STEPS[step_key]["required"]:
            print(f"\n  ✗ Required step '{STEPS[step_key]['label']}' failed — aborting.")
            break

    # Summary
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n{'=' * 56}")
    print(f"  Setup complete: {passed}/{total} steps succeeded")
    print(f"{'=' * 56}")
    print()

    for step_key, ok in results:
        icon = "✓" if ok else "✗"
        print(f"  {icon} {STEPS[step_key]['label']}")
    print()
    print(f"  Next: python -m cinematic_mood_weaver.main\n")

    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main())
