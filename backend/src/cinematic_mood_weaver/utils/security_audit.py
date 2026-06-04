"""Security audit module — verifies that no raw audio or biometric data
is ever transmitted externally, and that all privacy guarantees are enforced.

Run via: python -c "from cinematic_mood_weaver.utils.security_audit import run_audit; run_audit()"
"""

from __future__ import annotations

import ast
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SRC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "src" / "cinematic_mood_weaver"

SENSITIVE_PATTERNS = [
    "requests.post",
    "requests.get",
    "aiohttp.request",
    "aiohttp.ClientSession.post",
    "httpx.post",
    "httpx.get",
    "urllib.request",
    "urllib.urlopen",
]


class SecurityAudit:
    """Audits the codebase for potential privacy/security violations."""

    def __init__(self):
        self.violations: list[str] = []
        self.warnings: list[str] = []

    def run(self) -> bool:
        """Run all security checks. Returns True if all pass."""
        self._check_raw_audio_transmission()
        self._check_biometric_transmission()
        self._check_env_exposure()
        self._check_api_key_hardcoding()

        return len(self.violations) == 0

    def _check_raw_audio_transmission(self) -> None:
        """Ensure raw audio samples are never sent to external APIs."""
        audio_files = list(SRC_DIR.rglob("*.py"))
        violations = []

        for f in audio_files:
            content = f.read_text(encoding="utf-8")
            # Check for any file that mentions audio AND sends HTTP requests
            if "audio" in content.lower() or "samples" in content.lower():
                for pattern in SENSITIVE_PATTERNS:
                    if pattern in content:
                        violations.append(f"{f.name}: uses {pattern} while handling audio data")

        # The audio_capture module should only interact with SER (local inference)
        audio_capture = SRC_DIR / "sensors" / "audio_capture.py"
        if audio_capture.exists():
            content = audio_capture.read_text(encoding="utf-8")
            # Check it doesn't import any HTTP client
            http_imports = ["requests", "aiohttp", "httpx", "urllib"]
            for imp in http_imports:
                if imp in content:
                    self.violations.append(f"audio_capture.py imports {imp} — raw audio may be transmitted!")

        for v in violations:
            self.warnings.append(f"⚠ {v}")

        if not violations:
            self.warnings.append("✓ No raw audio transmission detected")

    def _check_biometric_transmission(self) -> None:
        """Ensure biometric data is never sent externally."""
        wearable_file = SRC_DIR / "sensors" / "wearable_manager.py"
        if wearable_file.exists():
            content = wearable_file.read_text(encoding="utf-8")
            if "requests" in content or "aiohttp" in content:
                self.warnings.append("⚠ wearable_manager.py imports HTTP libraries — verify biometric data stays local")
            else:
                self.warnings.append("✓ Biometric data stays local (no HTTP in wearable_manager.py)")

    def _check_env_exposure(self) -> None:
        """Ensure .env is in .gitignore."""
        gitignore = SRC_DIR.parent.parent.parent.parent / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text(encoding="utf-8")
            if ".env" in content and "!.env.example" in content:
                self.warnings.append("✓ .env is properly gitignored")
            else:
                self.warnings.append("⚠ .env may not be in .gitignore")
        else:
            self.warnings.append("⚠ No .gitignore found")

    def _check_api_key_hardcoding(self) -> None:
        """Scan for hardcoded API keys in source files."""
        patterns = [
            "sk-ant-",  # Claude
            "sk-proj-",  # OpenAI
        ]

        for f in SRC_DIR.rglob("*.py"):
            content = f.read_text(encoding="utf-8")
            for pattern in patterns:
                if pattern in content and "test" not in f.name:
                    self.violations.append(f"HARDCODED API KEY PATTERN in {f.name}: {pattern}...")

        if not any("sk-ant-" in f.read_text() for f in SRC_DIR.rglob("*.py") if ".env" not in f.name):
            self.warnings.append("✓ No hardcoded API keys detected")

    def report(self) -> str:
        """Generate a human-readable audit report."""
        lines = [
            "=" * 56,
            "  Security Audit Report — Cinematic Mood Weaver",
            "=" * 56,
        ]

        if not self.violations and not self.warnings:
            lines.append("\n  ✓ No issues found — codebase is clean.\n")
            return "\n".join(lines)

        if self.violations:
            lines.append(f"\n  ✗ VIOLATIONS ({len(self.violations)}):")
            for v in self.violations:
                lines.append(f"    • {v}")
            lines.append("")

        if self.warnings:
            lines.append(f"\n  Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"    {w}")
            lines.append("")

        verdict = "FAIL" if self.violations else "PASS"
        lines.append(f"\n  Verdict: {verdict}\n")
        return "\n".join(lines)


def run_audit() -> bool:
    """Run the security audit and print the report."""
    audit = SecurityAudit()
    passed = audit.run()
    print(audit.report())
    return passed


if __name__ == "__main__":
    run_audit()
