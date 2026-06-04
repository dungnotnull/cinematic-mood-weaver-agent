# Cinematic Mood Weaver — User Guide

## Quick Start (Desktop App)

1. **Install Python 3.11+** and run `python scripts/setup.py` from the `backend/` directory
2. **Configure API keys** via `python scripts/credentials_setup.py` (or skip — mock mode works)
3. **Start the server**: `python -m cinematic_mood_weaver.main --mode server`
4. **Open the frontend**: Point Tauri or a browser to the WebSocket server
5. **Click "Generate Mashup"** to get your first mood-based recommendation!

## Quick Start (Demo Mode)

```bash
cd backend
python -m cinematic_mood_weaver.main
# → Runs a demo cycle with synthetic data
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `python -m cinematic_mood_weaver.main --mode demo` | Single demo cycle |
| `python -m cinematic_mood_weaver.main --mode server` | Launch WebSocket server |
| `python scripts/setup.py` | Full Phase 0b setup |
| `python scripts/credentials_setup.py` | Interactive API key wizard |
| `python scripts/download_models.py` | Download SER models |
| `python scripts/benchmark_models.py` | Benchmarks inference speed |
| `python scripts/smoke_test.py` | Test all API connections |
| `python scripts/verify_health.py` | Full system health check |

## Feature Walkthrough

### 1. Mood Dashboard
- Displays current emotional state on a valence-arousal 2D map
- Shows recent mood history as a trend line
- Emotion color: happy (yellow), calm (green), anxious (orange), sad (indigo), angry (red)

### 2. Mashup Card
When you generate a mashup, you'll see:
- **Narrative**: LLM-generated explanation of why this content was chosen
- **Movie**: TMDB recommendation with poster, rating, and overview
- **Music**: Spotify playlists matched to your mood
- **Lighting**: Smart light scene with color temperature and brightness
- **Aromatherapy**: Diffuser oil profile recommendations

### 3. Feedback & Learning
- **Thumbs up/down**: Rates the mashup, trains your personal preference model
- **Mood override**: Manually correct your detected emotion if the system got it wrong
- The system learns your preferences over time and improves recommendations

## Privacy

- Raw audio is processed in RAM and immediately discarded — never written to disk
- Only anonymized emotion labels are sent to LLM APIs
- All stored data encrypted with AES-256-GCM
- Works fully offline with local Ollama + template fallback
