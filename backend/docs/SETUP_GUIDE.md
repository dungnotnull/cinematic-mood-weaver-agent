# Cinematic Mood Weaver — Setup Guide

## Prerequisites

- **Python 3.11+** (required for Torch compatibility)
- **Node.js 18+** (for frontend development)
- **Rust** (for Tauri desktop build — optional)
- **Ollama** (for offline LLM — optional)

## Full Setup

### 1. Python Backend

```bash
# Clone and enter
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Or use the automated script:
python scripts/setup.py
```

### 2. Configuration

```bash
# Interactive credential wizard:
python scripts/credentials_setup.py

# Or manually edit .env:
cp ../.env.example ../.env
# Edit with your API keys
```

### 3. Download SER Models (Optional — dummy models work for dev)

```bash
python scripts/download_models.py
# Add --dry-run to preview without downloading
# Add --resume to skip already-cached models
```

### 4. Verify Everything Works

```bash
# Quick smoke test:
python scripts/smoke_test.py

# Full health check:
python scripts/verify_health.py

# Run demo:
python -m cinematic_mood_weaver.main
```

### 5. Frontend (Tauri + React)

```bash
cd frontend
npm install
npm run dev      # Development server on :1420
# OR
npm run tauri dev  # Tauri desktop app
```

## API Key Registration Links

| Service | Required | Sign Up |
|---------|----------|---------|
| Claude API | Yes (recommended) | https://console.anthropic.com |
| Spotify API | Optional | https://developer.spotify.com/dashboard |
| TMDB API | Optional | https://www.themoviedb.org/settings/api |
| OpenAI API | Optional (fallback) | https://platform.openai.com/api-keys |
| Ollama | Optional (offline) | https://ollama.ai |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `sounddevice` fails to install | Install PortAudio: `brew install portaudio` (macOS), `apt install portaudio19-dev` (Linux) |
| PyTorch CUDA error | Install CPU-only torch: `pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| Tauri build fails | Install Rust via https://rustup.rs |
| WebSocket won't connect | Ensure backend is running: `python -m cinematic_mood_weaver.main --mode server` |
| Ollama not responding | Run `ollama pull mistral:7b` then `ollama serve` |
