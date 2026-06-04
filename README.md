<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/status-active--development-7c5cfc?style=for-the-badge">
    <img alt="Project Status" src="https://img.shields.io/badge/status-active--development-7c5cfc?style=for-the-badge">
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/github/license/dungnotnull/cinematic-mood-weaver-agent?style=for-the-badge&color=22c55e">
    <img alt="License MIT" src="https://img.shields.io/github/license/dungnotnull/cinematic-mood-weaver-agent?style=for-the-badge&color=22c55e">
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/python-3.11+-7c5cfc?style=for-the-badge&logo=python&logoColor=white">
    <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11+-7c5cfc?style=for-the-badge&logo=python&logoColor=white">
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/React-18-22c55e?style=for-the-badge&logo=react&logoColor=white">
    <img alt="React 18" src="https://img.shields.io/badge/React-18-22c55e?style=for-the-badge&logo=react&logoColor=white">
  </picture>
</p>

<h1 align="center">
  🎬 Cinematic Mood Weaver
</h1>

<p align="center">
  <em>Your Entertainment Director — Curated by Your Real-Time Emotional State</em>
</p>

<p align="center">
  <b>Speech Emotion Recognition</b> · <b>Biometric Fusion</b> · <b>LLM Orchestration</b> · <b>Smart Home</b> · <b>React/Tauri</b>
</p>

---

## 🌟 The Problem

Existing recommendation systems (Netflix, Spotify) rely on historical watch/listen behavior and shallow collaborative filtering — they suggest what you *usually* like, not what you *right now* need.

A user who just finished a stressful workday doesn't need "more content like what you watched last Tuesday."

**cinematic-mood-weaver-agent** solves the mismatch between real-time emotional state and entertainment curation by reading biometric and vocal signals to understand the user's current emotional condition, then orchestrating a holistic multi-sensory environment — movies + music + ambient lighting + aromatherapy — that either mirrors and validates that emotional state or guides the user toward a desired target mood. All without requiring any manual input.

## ✨ Features

### Core Pipeline

| Stage | Component | Description |
|-------|-----------|-------------|
| 🎤 **Sense** | `AudioCaptureModule` | Continuous microphone stream → 3s windowed chunks via `sounddevice` |
| 🧠 **Understand** | `SEREnsemble` | 3-model wav2vec2 ensemble for speech emotion recognition |
| 📍 **Map** | `EmotionMapper` | Probability vector → Russell's circumplex (valence, arousal) → emotion label |
| 🧬 **Fuse** | `BiometricFusion` | Weighted ensemble of SER + HRV/heart rate from wearables |
| 🎯 **Decide** | `InterventionSelector` | Mirror / Nudge / Transform — three tiers of mood intervention |
| 🤖 **Orchestrate** | `FallbackChain` | Claude API → GPT-4 → local Ollama → rule-based template |
| 🎬 **Curate** | `MashupSpec` | Structured JSON: movie + playlists + light scene + diffuser schedule |
| 🖥️ **Present** | `MoodDashboard` | Real-time valence-arousal plot + mashup card UI (React/Recharts) |

### Smart Features (Phase 2)

- **Wearable Integration** — BLE heart rate + HRV via `bleak` (Polar, Garmin, Apple Watch)
- **Mood Trajectory** — Linear regression predicts improving/declining/stable trends
- **Adaptive Sampling** — Dynamic SER polling: stable (300s) → volatile (60s) → shift (30s)
- **Confidence Gating** — Prompts user when SER confidence < 60%
- **Preference Learning** — Genre affinities learned from thumbs up/down feedback
- **Diversity Filter** — No repeat recommendations within 7-day window
- **Prompt Cache** — LLM context caching reduces API costs by ~80%

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CINEMATIC MOOD WEAVER AGENT                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────┐   ┌────────────────────────────────────┐ │
│  │     SENSING LAYER        │   │        STORAGE LAYER              │ │
│  │                          │   │                                    │ │
│  │  Microphone ──► SER      │   │  SQLite DB (AES-256 encrypted)    │ │
│  │  (wav2vec2 ensemble)     │   │  - mood_history                   │ │
│  │                          │   │  - preference_profiles            │ │
│  │  Wearable (BLE)          │   │  - mashup_feedback                │ │
│  │  - Heart Rate / HRV      │   │  - content_diversity             │ │
│  └───────────┬──────────────┘   └────────────────────────────────────┘ │
│              │                                                         │
│  ┌───────────▼──────────────────────────────────────────────────────┐ │
│  │              EMOTION PROCESSING LAYER                             │ │
│  │                                                                   │ │
│  │  SER Output ──► Valence-Arousal Mapper ──► Emotion Label         │ │
│  │  Biometric ──► Fusion Ensemble ──────────► Confidence Score      │ │
│  │  History ──► Trajectory Predictor ───────► Trend Direction       │ │
│  └───────────────────────────┬───────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────▼───────────────────────────────────────┐ │
│  │              LLM ORCHESTRATION LAYER (4-tier fallback)            │ │
│  │                                                                   │ │
│  │  Claude API ──► GPT-4 API ──► Local Ollama ──► Template           │ │
│  │                              │                                    │ │
│  │        Structured MashupSpec (validated JSON schema)              │ │
│  └───────────────────────────┬───────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────▼───────────────────────────────────────┐ │
│  │              CONTENT & ENVIRONMENT LAYER                           │ │
│  │                                                                   │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  ┌──────┐ │ │
│  │  │ TMDB API     │  │ Spotify API  │  │ Philips Hue   │  │ Aro- │ │ │
│  │  │ (Movies/TV)  │  │ (Playlists)  │  │ Home Assist.  │  │ ma-  │ │ │
│  │  └──────────────┘  └──────────────┘  └───────────────┘  └──────┘ │ │
│  └───────────────────────────┬───────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────▼───────────────────────────────────────┐ │
│  │              PRESENTATION LAYER (Tauri + React + TypeScript)      │ │
│  │                                                                   │ │
│  │  Mood Dashboard │ Mashup Card │ Feedback │ History │ Settings     │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## 🧠 How It Works (End-to-End Flow)

```
1. Audio Capture ──► 2. SER Inference ──► 3. Emotion State
         │                                        │
         │                                    ┌───▼────┐
         │                               Biometric Data? ←── Wearable (BLE)
         │                                    └───┬────┘
         │                                        │
         ▼                                        ▼
    Fusion Ensemble ──► (valence, arousal) ──► Emotion Label
                                                    │
                                                    ▼
    4. Intervention Selector ──► mirror / nudge / transform
                                                    │
                                                    ▼
    5. LLM Orchestration ──► Claude/GPT-4/Ollama/Template
                                                    │
                                                    ▼
                Structured MashupSpec (JSON)
                                                    │
             ┌──────────────────────────────────────┼──────────────┐
             ▼                                      ▼              ▼
    6. TMDB Search ──► 7. Spotify Search ──► 8. Light Scene
             │                                      │              │
             ▼                                      ▼              ▼
        Movie Recs                             Playlists      Hue/HA
                                                    │
                                                    ▼
    9. Mashup Card Rendered ──► Movie + Playlist + Lighting + Narrative
                                                    │
                                                    ▼
    10. User Feedback ──► Preference Learning ──► Better Next Time
```

## 💻 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Python 3.11+ | Core engine |
| **ML Inference** | HuggingFace `transformers` + PyTorch | wav2vec2 SER models |
| **Audio** | `sounddevice` + `librosa` | Microphone capture + preprocessing |
| **Biometrics** | `bleak` (BLE) | Wearable heart rate / HRV |
| **LLM** | `anthropic` / `openai` / `ollama` | Mashup orchestration |
| **Database** | SQLAlchemy + SQLite + `cryptography` | Mood history + preferences (AES-256 encrypted) |
| **Movie API** | TMDB | Movie/TV recommendations |
| **Music API** | Spotify Web API (`spotipy`) | Mood-matched playlists |
| **Smart Home** | `phue` + Home Assistant REST API | Lighting control |
| **Frontend** | React 18 + TypeScript + Vite | Desktop UI |
| **Charts** | Recharts | Valence-arousal mood dashboard |
| **Desktop** | Tauri (Rust) | Cross-platform desktop app |
| **IPC** | WebSocket (aiohttp) | Real-time backend ↔ frontend bridge |

### SER Models

| Model | Architecture | Accuracy | Purpose |
|-------|-------------|----------|---------|
| `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition` | wav2vec2-large-xlsr | 73.3% (RAVDESS) | Primary 8-class classifier |
| `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim` | wav2vec2-large | CCC 0.638 (valence) | Dimensional valence/arousal regression |
| `speechbrain/emotion-recognition-wav2vec2-IEMOCAP` | wav2vec2 + ECAPA | 79.1% (4-class IEMOCAP) | Ensemble validation |

## 🚀 Quick Start

### Prerequisites

- **Python** 3.11+
- **Node.js** 18+ (for frontend)
- **Rust** (for Tauri — optional, install via [rustup.rs](https://rustup.rs))

### One-shot Setup

```bash
# Clone
git clone https://github.com/dungnotnull/cinematic-mood-weaver-agent
cd cinematic-mood-weaver-agent

# Full automated setup
cd backend
python scripts/setup.py

# Or step by step:
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

```bash
# Interactive credential wizard (all are optional — mock mode works without them)
python scripts/credentials_setup.py

# Or manually:
cp .env.example .env
# Edit .env with your API keys
```

### Run the Demo

```bash
# Single demo cycle (synthetic data, no mic needed)
python -m cinematic_mood_weaver.main

# Launch server + WebSocket (for frontend connection)
python -m cinematic_mood_weaver.main --mode server
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev          # Vite dev server on :1420
# npm run tauri dev  # Native desktop app
```

### Verification

```bash
# Full system health check
python scripts/verify_health.py

# Quick API smoke test
python scripts/smoke_test.py

# Run all tests
set PYTHONPATH=src  # Windows
python -m pytest tests/ -v
```

## 📂 Project Structure

```
cinematic-mood-weaver-agent/
│
├── backend/
│   ├── src/cinematic_mood_weaver/
│   │   ├── types/           # Pydantic models (EmotionState, MashupSpec, etc.)
│   │   ├── db/              # SQLAlchemy ORM + CRUD service
│   │   ├── sensors/         # Audio capture + BLE wearable manager
│   │   ├── emotion/         # SER engine, mapper, fusion, trajectory, gates
│   │   ├── orchestration/   # Intervention selector, LLM backends, cost tracker
│   │   ├── clients/         # Spotify, TMDB, lighting API clients
│   │   ├── knowledge/       # Self-updating research crawler + model monitor
│   │   ├── utils/           # Encryption, scheduler, diversity filter, security audit
│   │   ├── websocket_server.py  # Real-time IPC with frontend
│   │   ├── pipeline.py      # End-to-end orchestrator
│   │   └── main.py          # Entry point (demo/server modes)
│   ├── scripts/             # Setup & verification scripts
│   ├── tests/               # 14 test files (59 unit + 4 integration)
│   └── docs/                # Setup guide & user guide
│
├── frontend/
│   ├── src/
│   │   ├── components/      # MoodDashboard, MashupCard, FeedbackButtons, Onboarding
│   │   ├── hooks/           # useMoodWeaver React hook
│   │   ├── types/           # TypeScript type definitions
│   │   └── utils/           # IPC bridge (WebSocket + mock)
│   └── src-tauri/           # Tauri desktop config + Rust sidecar
│
├── .github/workflows/       # CI pipeline
├── .env.example
├── .gitignore
└── README.md
```

## 🧪 Testing

```
tests/
├── test_units/              # 13 test files (59 tests)
│   ├── test_emotion_mapper.py     # Probability vector, VA mapping, fusion
│   ├── test_ser_engine.py         # Dummy model, ensemble behavior
│   ├── test_db_service.py         # CRUD, preferences, mashup log
│   ├── test_intervention.py       # Mirror/nudge/transform logic
│   ├── test_cost_tracker.py       # LLM costs, budget, prompt cache
│   ├── test_diversity_filter.py   # Seen content tracking
│   ├── test_confidence_gate.py    # Threshold gating, cooldown
│   ├── test_mood_trajectory.py    # Trend detection, shift detection
│   ├── test_adaptive_sampler.py   # Polling interval decisions
│   ├── test_encryption.py         # AES-256-GCM roundtrip
│   └── ...
└── test_integration/        # 1 test file (4 tests)
    └── test_e2e_pipeline.py       # Full pipeline, template fallback
```

```bash
# Run all tests
cd backend
set PYTHONPATH=src
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=term
```

## 🔒 Privacy & Security

| Data Type | Processing | Storage | Encryption | Transmitted? |
|-----------|-----------|---------|-----------|-------------|
| Raw audio | Local (RAM only) | Never persisted | Ephemeral | ❌ Never |
| Emotion labels | Local | SQLite | AES-256-GCM | ✅ Anonymized only |
| Biometric data | Local | SQLite | AES-256-GCM | ❌ Never |
| API keys | Local | `.env` / OS keychain | At rest | ❌ Never |

**Principles:**
- Raw audio is never written to disk — only the emotion inference result (a probability vector) is persisted
- All LLM API calls include only anonymized emotion labels and preference tags — no voice data, no biometrics
- Fully offline-capable with local Ollama + rule-based template fallback
- GDPR-compliant: export or delete all personal data at any time

## 📖 CLI Reference

```bash
# Backend modes
python -m cinematic_mood_weaver.main                   # Demo mode
python -m cinematic_mood_weaver.main --mode server     # WebSocket server

# Setup & verification
python scripts/setup.py                                # Full environment setup
python scripts/setup_env.py                            # Create venv + install deps
python scripts/credentials_setup.py                    # Interactive API key wizard
python scripts/download_models.py                      # Download SER models
python scripts/benchmark_models.py                     # CPU/CUDA benchmarks
python scripts/smoke_test.py                           # Test all API connections
python scripts/verify_health.py                        # Full system health check

# Security audit
python -m cinematic_mood_weaver.utils.security_audit
```

## 🗺️ Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| ✨ 0 | Code scaffold + environment setup | ✅ Complete |
| ⚡ 1 | MVP core loop (audio → emotion → mashup) | ✅ Complete |
| 🧠 2 | ML/AI smart features (trajectory, adaptive sampling, confidence gating, preference learning, diversity filter) | ✅ Complete |
| 🤖 3 | LLM integration (4-tier fallback chain, cost tracking, prompt caching) | ✅ Complete |
| 📚 4 | Self-updating knowledge brain (ArXiv/HuggingFace crawler, model monitor) | ✅ Complete |
| 🚀 5 | Testing, CI/CD, documentation, security audit, packaging | ✅ Complete |

### Advanced Features (Future)

- [ ] Facial expression fusion (webcam-based FER via `deepface`)
- [ ] Multi-user mood aggregation (households, couples)
- [ ] Personalized SER fine-tuning from user's voice samples (LoRA on wav2vec2)
- [ ] Smart TV casting (Google Cast / AirPlay)
- [ ] Generative content: music via MusicGen, wallpapers via Stable Diffusion
- [ ] Sleep transition protocol (gradual 2-hour wind-down)
- [ ] Therapist dashboard (shareable mood trend PDF reports)
- [ ] Cross-device session sync (phone ↔ desktop ↔ TV)

## 🏗️ Built With

- [wav2vec 2.0](https://arxiv.org/abs/2006.11477) — Self-supervised speech representations
- [HuggingFace Transformers](https://github.com/huggingface/transformers) — ML model inference
- [Tauri](https://tauri.app) — Lightweight desktop framework (Rust + web)
- [Recharts](https://recharts.org) — Composable React charting
- [SQLAlchemy](https://www.sqlalchemy.org) — Python ORM
- [APScheduler](https://github.com/agronholm/apscheduler) — Task scheduling
- [crawl4ai](https://github.com/unclecode/crawl4ai) — AI-powered web crawler

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Russell's Circumplex Model of Affect** (1980) — The 2D valence-arousal emotion space that underpins our emotion mapping
- **Rosalind Picard** — *Affective Computing* (MIT Press, 1997) — The foundational vision for machines that sense and respond to emotion
- **Mood Congruence Effect** — Knobloch & Zillmann (2002) — The theoretical basis for mirror vs. transform intervention modes

---

<p align="center">
  Made with ❤️ and 🧠 — for when algorithms should understand how you feel, not just what you clicked.
</p>
