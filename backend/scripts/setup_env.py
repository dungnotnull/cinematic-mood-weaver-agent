"""Phase 0b — Python environment setup script.

Creates a virtual environment, installs all pinned dependencies,
and verifies the Python version meets minimum requirements.
Supports --dry-run for development without actual installation.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


REQUIRED_PYTHON = (3, 11)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
VENV_DIR = PROJECT_ROOT / ".venv"


def log_step(msg: str) -> None:
    print(f"  ▶ {msg}")


def log_ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def log_skip(msg: str) -> None:
    print(f"  ⊘ {msg}")


def log_error(msg: str) -> None:
    print(f"  ✗ {msg}")


def check_python_version() -> bool:
    """Verify Python >= 3.11."""
    v = sys.version_info
    ok = v >= REQUIRED_PYTHON
    if ok:
        log_ok(f"Python {v.major}.{v.minor}.{v.micro} (≥ {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]})")
    else:
        log_error(f"Python {v.major}.{v.minor} is too old; need ≥ {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}")
    return ok


def create_venv(dry_run: bool) -> Path:
    """Create .venv if it doesn't exist."""
    if VENV_DIR.exists():
        log_ok(f"Virtual environment exists at {VENV_DIR}")
        return VENV_DIR

    if dry_run:
        log_skip(f"Would create venv at {VENV_DIR}")
        return VENV_DIR

    log_step("Creating virtual environment...")
    venv.create(VENV_DIR, with_pip=True, clear=False)
    log_ok(f"Virtual environment created at {VENV_DIR}")
    return VENV_DIR


def get_python(venv_path: Path) -> str:
    """Return the path to the venv's python executable."""
    if sys.platform == "win32":
        return str(venv_path / "Scripts" / "python.exe")
    return str(venv_path / "bin" / "python")


def install_requirements(venv_path: Path, dry_run: bool) -> bool:
    """Install pinned dependencies from requirements.txt."""
    if not REQUIREMENTS.exists():
        log_skip(f"requirements.txt not found at {REQUIREMENTS}")
        return True

    if dry_run:
        log_skip(f"Would install {REQUIREMENTS.name} into {venv_path}")
        return True

    python = get_python(venv_path)
    log_step(f"Installing from {REQUIREMENTS.name}...")

    result = subprocess.run(
        [python, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )

    if result.returncode == 0:
        log_ok(f"All {REQUIREMENTS.name} packages installed")
        return True
    else:
        log_error(f"pip install failed:\n{result.stderr}")
        return False


def upgrade_pip(venv_path: Path, dry_run: bool) -> None:
    """Ensure pip is up to date in the venv."""
    if dry_run:
        log_skip("Would upgrade pip")
        return

    python = get_python(venv_path)
    subprocess.run(
        [python, "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True, cwd=PROJECT_ROOT,
    )
    log_ok("pip upgraded to latest")


def create_app_data_dir(dry_run: bool) -> None:
    """Create ~/.cinematic-mood-weaver/ directory tree."""
    from pathlib import Path as P
    data_dir = P.home() / ".cinematic-mood-weaver"
    subdirs = ["logs", "models"]

    if dry_run:
        log_skip(f"Would create {data_dir}/ with subdirs: {subdirs}")
        return

    data_dir.mkdir(parents=True, exist_ok=True)
    for sub in subdirs:
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    log_ok(f"App data directory ready at {data_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up Cinematic Mood Weaver Python environment")
    parser.add_argument("--dry-run", action="store_true", help="Preview steps without executing")
    args = parser.parse_args()

    print("=" * 56)
    print("  Cinematic Mood Weaver — Environment Setup")
    print("=" * 56)

    ok = True
    ok = check_python_version() and ok

    venv_path = create_venv(args.dry_run)
    if not args.dry_run and not VENV_DIR.exists():
        log_error("Virtual environment creation failed")
        return 1

    upgrade_pip(venv_path, args.dry_run)
    ok = install_requirements(venv_path, args.dry_run) and ok
    create_app_data_dir(args.dry_run)

    print()
    if ok:
        if args.dry_run:
            print("  ✓ All checks passed (dry run) — ready for real execution.\n")
        else:
            activate = ".venv\\Scripts\\activate" if sys.platform == "win32" else "source .venv/bin/activate"
            print(f"  ✓ Environment ready. Activate it:\n      {activate}\n")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
