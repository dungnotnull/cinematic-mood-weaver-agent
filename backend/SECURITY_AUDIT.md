# Security Audit — Cinematic Mood Weaver

Last run: Automated (via `python -m cinematic_mood_weaver.utils.security_audit`)

## Privacy Guarantees

| Data Type | Processing Location | Storage | Encryption | Transmitted? |
|-----------|-------------------|---------|-----------|-------------|
| Raw audio | Local (RAM only) | Never persisted | N/A (ephemeral) | ❌ No |
| Emotion labels | Local | SQLite | AES-256-GCM | ✅ Anonymized only |
| Biometric data | Local | SQLite | AES-256-GCM | ❌ No |
| User preferences | Local | SQLite | AES-256-GCM | ❌ No |
| API keys | Local | `.env` / OS keychain | At rest | ❌ No |

## Design Principles Enforced

1. **Raw audio is never written to disk** — only the emotion inference result (a probability vector) is persisted. The `AudioCaptureModule` processes 3-second rolling windows in RAM and discards them.

2. **No raw audio or biometrics in LLM calls** — the LLM context includes only anonymized emotion labels and preference tags. See `llm_backends.py` `_build_context()` for the exact data sent.

3. **Fully offline-capable** — Ollama backend + template fallback mean zero cloud dependency for core functionality.

4. **GDPR-compliant** — All personal data stored in `~/.cinematic-mood-weaver/data.db`, encrypted with AES-256-GCM. Export or delete with one command.

## Verified By Code

- `security_audit.py` — Static analysis checks for:
  - No HTTP libraries imported in `audio_capture.py` or `wearable_manager.py`
  - No hardcoded API keys in source files
  - `.env` properly gitignored
