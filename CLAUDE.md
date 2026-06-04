# CLAUDE.md — cinematic-mood-weaver-agent

## Project Identity
- **Name:** cinematic-mood-weaver-agent
- **Tagline:** Your Entertainment Director — Curated by Your Real-Time Emotional State
- **Current Status:** Phase 0 — Research & Environment Setup
- **Last Updated:** 2026-06-03

---

## Core Problem Being Solved
Existing recommendation systems (Netflix, Spotify) rely on historical watch/listen behavior and shallow collaborative filtering — they suggest what you *usually* like, not what you *right now* need. A user who just finished a stressful workday doesn't need "more content like what you watched last Tuesday." This agent solves the mismatch between real-time emotional state and entertainment curation by reading biometric and vocal signals to understand the user's current emotional condition, then orchestrating a holistic multi-sensory environment (movies + music + ambient lighting + aromatherapy) that either mirrors and validates that emotional state or guides the user toward a desired target mood — all without requiring any manual input.

---

## Architecture Summary
- **Platform:** Cross-platform desktop app (Python backend + Electron/Tauri frontend) with optional mobile companion
- **ML Stack:** Local Speech Emotion Recognition (SER) DL model via HuggingFace Transformers + optional wearable biometric input (heart rate, HRV, EDA)
- **Local SLM:** Small LLM (Mistral 7B via Ollama) for offline context synthesis and smart home prompt generation
- **External APIs:** Spotify Web API, JustWatch/TMDB API (movie discovery), Philips Hue / Home Assistant (smart lighting), Claude API or GPT-4 (cloud LLM backend)

---

## Key Technical Decisions
1. **SER as primary emotion signal**: Audio analysis via wav2vec2-based SER model is the core sensing layer — more accessible than wearables, works without any hardware beyond a microphone
2. **Biometric fusion as enhancement layer**: When wearable data (heart rate, HRV) is available, it is fused with SER output using a lightweight ensemble to improve accuracy
3. **Local-first processing**: All audio and biometric data is processed on-device; only anonymized emotion labels are ever sent to external APIs
4. **Pluggable LLM backend**: Claude API → GPT-4 → local Ollama fallback chain for environment orchestration prompt generation
5. **Mashup output model**: Output is not a single recommendation but a synchronized multi-channel bundle (film + playlist + light scene + diffuser schedule)
6. **Graduated mood intervention**: Three-tier system — mirror (match current mood), nudge (gentle shift), transform (strong redirect toward target)
7. **Emotion vector space**: Emotions are mapped to a 2D valence-arousal space (Russell's circumplex model) enabling smooth interpolation between states

---

## External LLM API Integrations

| Provider | Purpose | Config Key | Model |
|----------|---------|-----------|-------|
| Anthropic Claude | Context extraction, mashup narrative, smart home prompt | `CLAUDE_API_KEY` | claude-sonnet-4-6 |
| OpenAI GPT-4 | Fallback LLM for mashup orchestration | `OPENAI_API_KEY` | gpt-4o |
| Local Ollama | Offline fallback, no API key needed | `OLLAMA_BASE_URL` | mistral:7b |

---

## HuggingFace Models in Use

| Model ID | Purpose | Link |
|----------|---------|------|
| `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition` | Primary SER — 7-class emotion from voice | https://huggingface.co/ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition |
| `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim` | Dimensional (valence/arousal) emotion from speech | https://huggingface.co/audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim |
| `speechbrain/emotion-recognition-wav2vec2-IEMOCAP` | IEMOCAP-trained SER cross-validation | https://huggingface.co/speechbrain/emotion-recognition-wav2vec2-IEMOCAP |
| `facebook/wav2vec2-base-960h` | Base audio feature extractor | https://huggingface.co/facebook/wav2vec2-base-960h |
| `distilbert-base-uncased` | Text-based emotion fallback (typed input) | https://huggingface.co/distilbert-base-uncased |

---

## Current Active Development Tasks
- [ ] Set up Python virtual environment and install core dependencies
- [ ] Download and benchmark SER models (ehcalabres, audeering, speechbrain)
- [ ] Build audio capture module (microphone → 3s window → emotion vector)
- [ ] Implement valence-arousal 2D mapping and mood-state classifier
- [ ] Create Spotify API wrapper (playlist search by mood/genre/tempo)
- [ ] Create TMDB API wrapper (movie discovery by mood tags/genres)
- [ ] Build Philips Hue / Home Assistant lighting scene controller
- [ ] Design LLM orchestration prompt template for mashup generation
- [ ] Implement local SQLite store for user mood history and preference learning
- [ ] Build Electron/Tauri frontend UI (mood dashboard + mashup display)

---

## Related Files
- `PROJECT-detail.md` — Full technical specification and feature list
- `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` — Phase roadmap with milestones
- `SECOND-KNOWLEDGE-BRAIN.md` — Research papers, SOTA models, self-update protocol
