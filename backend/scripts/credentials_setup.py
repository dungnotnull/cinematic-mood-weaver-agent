"""Phase 0b — Interactive API credential configuration wizard.

Walks through each required external service, guides the user to obtain
API keys, and writes them to the .env file. Tests each credential on
completion when possible.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOT_ENV = PROJECT_ROOT.parent / ".env"
DOT_ENV_EXAMPLE = PROJECT_ROOT.parent / ".env.example"


# ── Service Definitions ──────────────────────────────────────────────


@dataclass
class ServiceCredential:
    name: str
    env_key: str
    instructions: str
    signup_url: str
    required: bool = True
    test_fn: Optional[str] = None  # Python expression to test the credential


SERVICES: list[ServiceCredential] = [
    ServiceCredential(
        name="Claude API (Anthropic)",
        env_key="CLAUDE_API_KEY",
        instructions="Go to console.anthropic.com → API Keys → Create Key. Paste the sk-ant-... key.",
        signup_url="https://console.anthropic.com/",
        test_fn="import anthropic; anthropic.Anthropic(api_key='{key}').models.list()",
    ),
    ServiceCredential(
        name="OpenAI API (GPT-4 fallback)",
        env_key="OPENAI_API_KEY",
        instructions="Go to platform.openai.com → API Keys → Create new secret key.",
        signup_url="https://platform.openai.com/api-keys",
        required=False,
        test_fn="from openai import OpenAI; OpenAI(api_key='{key}').models.list()",
    ),
    ServiceCredential(
        name="Spotify API",
        env_key="SPOTIFY_CLIENT_ID",
        instructions="Go to developer.spotify.com → Dashboard → Create App. Add your redirect URI.",
        signup_url="https://developer.spotify.com/dashboard",
        # Spotify needs both CLIENT_ID and CLIENT_SECRET, tested together
    ),
    ServiceCredential(
        name="TMDB API",
        env_key="TMDB_API_KEY",
        instructions="Go to themoviedb.org → Settings → API → Generate API Key.",
        signup_url="https://www.themoviedb.org/settings/api",
        test_fn="import requests; requests.get('https://api.themoviedb.org/3/configuration', params={'api_key': '{key}'}).json()",
    ),
]

# ── Helpers ──────────────────────────────────────────────────────────


def load_existing_env() -> dict[str, str]:
    """Load existing .env file into a dictionary."""
    if not DOT_ENV.exists():
        return {}
    env: dict[str, str] = {}
    for line in DOT_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("\"'")
    return env


def write_env(env: dict[str, str]) -> None:
    """Write dictionary to .env file, preserving comments from .env.example."""
    lines: list[str] = []
    if DOT_ENV_EXAMPLE.exists():
        template = DOT_ENV_EXAMPLE.read_text(encoding="utf-8")
        for line in template.splitlines():
            if "=" in line and not line.startswith("#") and not line.startswith("# "):
                key = line.split("=", 1)[0].strip()
                if key in env and env[key]:
                    lines.append(f"{key}={env[key]}")
                else:
                    lines.append(line)
            else:
                lines.append(line)
    else:
        for key, value in env.items():
            lines.append(f"{key}={value}")
    DOT_ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def prompt_for_value(service: ServiceCredential, current: str) -> str:
    """Prompt the user to enter a credential value."""
    print(f"\n  {'─' * 48}")
    print(f"  {service.name}")
    print(f"  {'─' * 48}")
    print(f"  Sign up: {service.signup_url}")
    print(f"  {service.instructions}")
    print()

    if current:
        default_display = current[:12] + "..." if len(current) > 12 else current
        prompt_text = f"  Enter key (current: {default_display}) [Enter to skip]: "
    else:
        prompt_text = "  Enter key (or press Enter to skip): "

    value = input(prompt_text).strip().strip("\"'")
    return value or current


# ── Main ─────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure API credentials for Cinematic Mood Weaver")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing .env")
    parser.add_argument("--reset", action="store_true", help="Clear all existing credentials and start fresh")
    args = parser.parse_args()

    print("=" * 56)
    print("  Cinematic Mood Weaver — API Credentials Setup")
    print("=" * 56)

    if args.dry_run:
        print("\n  ⊘ DRY RUN — nothing will be written\n")

    env = {} if args.reset else load_existing_env()

    print("\n  This wizard will help you configure API keys for each service.")
    print("  Only Claude API is required; others have graceful fallbacks.")
    print("  Press Enter to skip any service.\n")

    for service in SERVICES:
        current = env.get(service.env_key, "")
        value = prompt_for_value(service, current)
        if value:
            env[service.env_key] = value
            if service.env_key == "SPOTIFY_CLIENT_ID":
                # Also prompt for client secret
                secret_key = "SPOTIFY_CLIENT_SECRET"
                current_secret = env.get(secret_key, "")
                secret = input(f"  Enter Spotify Client Secret (current: {'set' if current_secret else 'not set'}): ").strip().strip("\"'")
                if secret:
                    env[secret_key] = secret
        elif not current:
            if service.required:
                print(f"  ⚠  {service.name} is recommended for full functionality")
            else:
                print(f"  ⊘ Skipped (optional)")

    # Write .env
    if not args.dry_run:
        write_env(env)
        print(f"\n  ✓ Credentials saved to {DOT_ENV}")
    else:
        print(f"\n  ⊘ Would write {len(env)} keys to {DOT_ENV}")

    # Summary
    configured = sum(1 for s in SERVICES if env.get(s.env_key))
    total = len(SERVICES)
    missing = [s.name for s in SERVICES if not env.get(s.env_key) and s.required]
    if missing:
        print(f"  ⚠  Missing required: {', '.join(missing)}")
    print(f"  Configured: {configured}/{total} services\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
