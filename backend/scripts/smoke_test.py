"""Phase 0b — Smoke tests for all external API credentials and local services.

Verifies each configured API endpoint is reachable and returns valid responses.
Runs all checks independently and reports pass/fail per service.
Supports --dry-run to show what would be tested without making real calls.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import requests as http_requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_env() -> dict[str, str]:
    """Load .env file from project root parent."""
    env_path = PROJECT_ROOT.parent / ".env"
    if not env_path.exists():
        return {}
    env: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("\"'")
    return env


def check(ok: bool, label: str, detail: str = "") -> None:
    """Print a formatted check result."""
    icon = "✓" if ok else "✗"
    detail_str = f" — {detail}" if detail else ""
    print(f"  {icon} {label}{detail_str}")


def test_claude_api(api_key: str, dry_run: bool) -> bool:
    """Verify Claude API key works."""
    if dry_run:
        check(True, "Claude API", "dry run, would test key")
        return True
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "say ok"}],
        )
        ok = len(response.content) > 0
        check(ok, "Claude API", "key valid, response received" if ok else "unexpected response")
        return ok
    except ImportError:
        check(False, "Claude API", "anthropic SDK not installed")
        return False
    except Exception as e:
        check(False, "Claude API", str(e)[:60])
        return False


def test_openai_api(api_key: str, dry_run: bool) -> bool:
    """Verify OpenAI API key works."""
    if not api_key:
        check(True, "OpenAI API", "not configured (optional, skipped)")
        return True
    if dry_run:
        check(True, "OpenAI API", "dry run, would test key")
        return True
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=10,
            messages=[{"role": "user", "content": "say ok"}],
        )
        ok = len(response.choices) > 0
        check(ok, "OpenAI API", "key valid" if ok else "unexpected response")
        return ok
    except ImportError:
        check(False, "OpenAI API", "openai SDK not installed")
        return False
    except Exception as e:
        check(False, "OpenAI API", str(e)[:60])
        return False


def test_ollama(dry_run: bool) -> bool:
    """Verify local Ollama instance is running and reachable."""
    if dry_run:
        check(True, "Ollama", "dry run, would test local connection")
        return True
    try:
        resp = http_requests.get("http://localhost:11434/api/tags", timeout=3)
        ok = resp.status_code == 200
        models = [m["name"] for m in resp.json().get("models", [])]
        detail = f"running, {len(models)} models available" if ok else f"status {resp.status_code}"
        check(ok, "Ollama", detail)
        return ok
    except Exception as e:
        check(False, "Ollama", f"not reachable — {str(e)[:60]}")
        return False


def test_spotify(client_id: str, client_secret: str, dry_run: bool) -> bool:
    """Verify Spotify API credentials."""
    if not client_id or not client_secret:
        check(True, "Spotify API", "not configured (optional, skipped)")
        return True
    if dry_run:
        check(True, "Spotify API", "dry run, would test credentials")
        return True
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        auth = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(auth_manager=auth)
        results = sp.search(q="mood", type="playlist", limit=1)
        ok = len(results.get("playlists", {}).get("items", [])) > 0
        check(ok, "Spotify API", "credentials valid, search returned results" if ok else "search returned empty")
        return ok
    except ImportError:
        check(False, "Spotify API", "spotipy SDK not installed")
        return False
    except Exception as e:
        check(False, "Spotify API", str(e)[:60])
        return False


def test_tmdb(api_key: str, dry_run: bool) -> bool:
    """Verify TMDB API key."""
    if not api_key:
        check(True, "TMDB API", "not configured (optional, skipped)")
        return True
    if dry_run:
        check(True, "TMDB API", "dry run, would test key")
        return True
    try:
        resp = http_requests.get(
            "https://api.themoviedb.org/3/configuration",
            params={"api_key": api_key},
            timeout=5,
        )
        ok = resp.status_code == 200
        detail = "key valid" if ok else f"HTTP {resp.status_code}"
        check(ok, "TMDB API", detail)
        return ok
    except Exception as e:
        check(False, "TMDB API", str(e)[:60])
        return False


def test_hue_bridge(ip: str, dry_run: bool) -> bool:
    """Verify Philips Hue bridge is reachable."""
    if not ip:
        check(True, "Philips Hue", "not configured (optional, skipped)")
        return True
    if dry_run:
        check(True, "Philips Hue", "dry run, would ping bridge")
        return True
    try:
        resp = http_requests.get(f"http://{ip}/description.xml", timeout=3)
        ok = resp.status_code == 200
        check(ok, "Philips Hue", f"bridge reachable at {ip}" if ok else f"HTTP {resp.status_code}")
        return ok
    except Exception as e:
        check(False, "Philips Hue", str(e)[:60])
        return False


def test_python_deps(dry_run: bool) -> bool:
    """Verify all core Python dependencies are importable."""
    required = [
        "torch", "transformers", "sounddevice", "librosa",
        "spotipy", "anthropic", "openai", "sqlalchemy",
        "cryptography", "pydantic", "pydantic_settings",
        "aiohttp", "apscheduler",
    ]

    if dry_run:
        check(True, "Python deps", f"dry run, would check {len(required)} packages")
        return True

    missing: list[str] = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)

    ok = len(missing) == 0
    detail = "all installed" if ok else f"missing: {', '.join(missing)}"
    check(ok, "Python dependencies", detail)
    return ok


def test_database(dry_run: bool) -> bool:
    """Verify SQLite database initializes correctly."""
    if dry_run:
        check(True, "Database", "dry run, would initialize SQLite schema")
        return True
    try:
        from cinematic_mood_weaver.db.engine import init_db
        init_db()
        check(True, "Database", "SQLite schema initialized")
        return True
    except Exception as e:
        check(False, "Database", str(e)[:60])
        return False


def test_pipeline_import(dry_run: bool) -> bool:
    """Verify the main pipeline module imports without errors."""
    if dry_run:
        check(True, "Pipeline import", "dry run, would import pipeline module")
        return True
    try:
        from cinematic_mood_weaver.pipeline import MoodWeaverPipeline  # noqa: F401
        check(True, "Pipeline import", "module loaded successfully")
        return True
    except Exception as e:
        check(False, "Pipeline import", str(e)[:60])
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test Cinematic Mood Weaver system health")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be tested without making real calls")
    args = parser.parse_args()

    print("=" * 56)
    print("  Cinematic Mood Weaver — System Smoke Test")
    print("=" * 56)

    env = load_env()

    if args.dry_run:
        print("\n  ⊘ DRY RUN — no real API calls or imports will be made\n")
    else:
        print("\n  Testing all configured services...\n")

    results: list[bool] = []

    # Local services
    print("  ── Local Environment ──")
    results.append(test_python_deps(args.dry_run))
    results.append(test_database(args.dry_run))
    results.append(test_pipeline_import(args.dry_run))
    print()

    # LLM APIs
    print("  ── LLM APIs ──")
    results.append(test_claude_api(env.get("CLAUDE_API_KEY", ""), args.dry_run))
    results.append(test_openai_api(env.get("OPENAI_API_KEY", ""), args.dry_run))
    results.append(test_ollama(args.dry_run))
    print()

    # Content APIs
    print("  ── Content APIs ──")
    results.append(test_spotify(
        env.get("SPOTIFY_CLIENT_ID", ""),
        env.get("SPOTIFY_CLIENT_SECRET", ""),
        args.dry_run,
    ))
    results.append(test_tmdb(env.get("TMDB_API_KEY", ""), args.dry_run))
    print()

    # Smart home
    print("  ── Smart Home ──")
    results.append(test_hue_bridge(env.get("HUE_BRIDGE_IP", ""), args.dry_run))

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r)
    failed = total - passed
    print(f"\n  {'─' * 48}")
    print(f"  Result: {passed}/{total} checks passed", end="")
    if failed:
        print(f", {failed} failed")
    else:
        print()
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
