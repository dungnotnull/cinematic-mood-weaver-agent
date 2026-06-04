# Cinematic Mood Weaver — Backend

AI-driven multi-sensory entertainment orchestration system. Reads real-time emotional state via voice (Speech Emotion Recognition) and optional biometrics, then curates synchronized movie + music + lighting + aromatherapy mashup bundles.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
cp ../.env.example ../.env
# Edit .env with your API keys

# 4. Run the demo
python -m cinematic_mood_weaver.main
```

## Project Structure

```
backend/
├── src/
│   └── cinematic_mood_weaver/
│       ├── types/          # Pydantic models (EmotionState, MashupSpec, etc.)
│       ├── db/             # SQLAlchemy models, engine, CRUD service
│       ├── sensors/        # Audio capture (sounddevice microphone stream)
│       ├── emotion/        # SER engine, emotion mapper, biometric fusion
│       ├── orchestration/  # Intervention selector, LLM backends, fallback chain
│       ├── clients/        # Spotify, TMDB, Philips Hue / Home Assistant
│       ├── utils/          # Encryption, logging, scheduler
│       ├── config.py       # pydantic-settings configuration
│       ├── pipeline.py     # End-to-end pipeline orchestrator
│       └── main.py         # CLI entry point and demo cycle
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Pipeline Flow

```
Audio Capture → SER Inference → Emotion State → Intervention Mode
    → LLM Mashup Spec → Spotify + TMDB + Lighting APIs → Mashup Result
```

## Architecture Decisions

- **Dummy SER models** for development — switch to real HuggingFace models with `SEREnsemble(use_dummy=False)` when ready
- **LLM fallback chain**: Claude API → GPT-4 → local Ollama → rule-based template (always works)
- **Graceful degradation**: No API credentials needed for development — dummy data fills in
- **Local-first**: Raw audio never persists; all processing on-device
