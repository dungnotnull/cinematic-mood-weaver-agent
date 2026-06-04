# PROJECT-detail.md — cinematic-mood-weaver-agent

## Executive Summary
cinematic-mood-weaver-agent is an AI-driven multi-sensory entertainment orchestration system that replaces passive, history-based content recommendation with active, real-time emotional state detection. By analyzing the user's voice and optionally their biometric signals, the agent identifies their current emotional condition on a 2D valence-arousal map, then autonomously curates and synchronizes a multi-channel environment bundle: a movie selection, music playlist, smart lighting scene, and aromatherapy diffuser schedule. The result is an entertainment experience that responds to how the user actually feels right now — not what an algorithm assumes they like based on past behavior.

---

## Problem Statement
Streaming platforms have fundamentally broken the feedback loop between human emotion and content delivery. Netflix's recommendation engine optimizes for watch-time maximization and engagement retention, not emotional wellbeing. Spotify's Discover Weekly is driven by audio feature similarity and collaborative filtering — it cannot tell the difference between a user who wants to feel energized and one who needs to decompress.

**Key pain points backed by research:**
- A 2023 Nielsen report found 58% of streaming users spend more than 10 minutes choosing what to watch, often ending up watching nothing ("decision fatigue paralysis")
- The APA's 2024 Stress in America survey found 67% of adults use entertainment as a primary stress regulation tool, yet report frequently choosing content that worsens their mood
- Affective computing research (Picard, MIT Media Lab) has demonstrated that real-time physiological signals can predict emotional state with >80% accuracy — yet no mainstream platform uses this data
- The "emotional congruence effect" in psychology shows that mood-matched media consumption is significantly more effective for emotional regulation than algorithmically random recommendations

The gap: all the signal intelligence needed to solve this exists (SER models, HRV sensors, smart home APIs) but no product has connected them into a unified orchestration layer.

---

## Target Users & Use Cases

**Primary Users:**
- **Stressed knowledge workers**: Finish a difficult workday and need a curated wind-down experience without cognitive effort
- **People managing mood disorders**: Individuals with anxiety or mild depression who use entertainment therapeutically and need mood-matched curation
- **Smart home enthusiasts**: Early adopters with Philips Hue, Sonos, and wearables who want deeper integration of their environment
- **Wellness-focused individuals**: People who track HRV, sleep, and stress and want their environment to respond to their data

**Use Cases:**
1. "Stress decompression": High cortisol detected → agent creates calming bundle (slow cinema, lo-fi music, warm dim lighting, lavender diffuser)
2. "Energy boost": Low arousal detected → agent creates energizing bundle (action film, upbeat playlist, cool bright lighting)
3. "Focus mode": User specifies target mood → agent generates focus environment (documentary, ambient music, neutral white lighting)
4. "Social gathering": Multiple users detected → agent aggregates mood signals and finds consensus entertainment
5. "Bedtime transition": Evening biometrics detected → graduated shift toward sleep-promoting content bundle

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CINEMATIC MOOD WEAVER AGENT                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────┐   ┌─────────────────────────────┐  │
│  │     SENSING LAYER           │   │     STORAGE LAYER           │  │
│  │                             │   │                             │  │
│  │  Microphone ──► SER Model   │   │  SQLite DB                  │  │
│  │  (wav2vec2-based)           │   │  - mood_history             │  │
│  │                             │   │  - preference_profiles      │  │
│  │  Wearable API (optional)    │   │  - mashup_feedback          │  │
│  │  - Heart Rate               │   │  - content_ratings          │  │
│  │  - HRV / Stress             │   │                             │  │
│  │  - EDA (skin conductance)   │   │  AES-256 encrypted          │  │
│  └──────────────┬──────────────┘   └─────────────────────────────┘  │
│                 │                                                     │
│  ┌──────────────▼──────────────────────────────────────────────────┐ │
│  │              EMOTION PROCESSING LAYER                           │ │
│  │                                                                  │ │
│  │  SER Output ──► Valence-Arousal Mapper ──► Emotion State Label  │ │
│  │  Biometric ──► Fusion Ensemble ──────────► Confidence Score     │ │
│  │                                            └──► Mood History     │ │
│  └──────────────────────────────┬───────────────────────────────────┘ │
│                                 │                                     │
│  ┌──────────────────────────────▼───────────────────────────────────┐ │
│  │              LLM ORCHESTRATION LAYER                             │ │
│  │                                                                  │ │
│  │  Emotion State + User Prefs + History                           │ │
│  │       │                                                          │ │
│  │       ▼                                                          │ │
│  │  Claude API / GPT-4 / Ollama (fallback chain)                   │ │
│  │       │                                                          │ │
│  │       ▼                                                          │ │
│  │  Structured Mashup Spec (JSON):                                  │ │
│  │  { mood_target, film_query, music_query,                        │ │
│  │    light_scene, diffuser_profile, narrative }                   │ │
│  └──────────────────────────────┬───────────────────────────────────┘ │
│                                 │                                     │
│  ┌──────────────────────────────▼───────────────────────────────────┐ │
│  │              CONTENT & ENVIRONMENT LAYER                         │ │
│  │                                                                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌───────┐  │ │
│  │  │ TMDB / Just │  │  Spotify    │  │ Philips Hue  │  │SwitchB│  │ │
│  │  │ Watch API   │  │  Web API    │  │ Home Assist. │  │ ot /  │  │ │
│  │  │ (Movies/TV) │  │ (Playlists) │  │ (Lighting)   │  │Diffuse│  │ │
│  │  └─────────────┘  └─────────────┘  └──────────────┘  └───────┘  │ │
│  └──────────────────────────────┬───────────────────────────────────┘ │
│                                 │                                     │
│  ┌──────────────────────────────▼───────────────────────────────────┐ │
│  │              PRESENTATION LAYER (Electron/Tauri UI)              │ │
│  │  Mood Dashboard │ Mashup Card │ Feedback Buttons │ History View   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology | Source |
|-----------|-----------|--------|
| Core backend | Python 3.11+ | python.org |
| Audio capture | `sounddevice` + `librosa` | PyPI |
| SER inference | HuggingFace `transformers` + PyTorch | huggingface.co |
| Biometric integration | `bleak` (BLE), Garmin Connect IQ SDK | Various |
| LLM orchestration | `anthropic` SDK, `openai` SDK, `ollama` client | PyPI |
| Movie discovery | TMDB API (themoviedb.org) | themoviedb.org |
| Music playlists | Spotify Web API (`spotipy`) | developer.spotify.com |
| Smart lighting | `phue` (Philips Hue), Home Assistant REST API | PyPI / HA docs |
| Aromatherapy control | SwitchBot API, custom BLE diffuser | SwitchBot SDK |
| Local database | SQLite3 via `sqlalchemy` | PyPI |
| Encryption | `cryptography` (AES-256-GCM) | PyPI |
| Frontend | Tauri (Rust + React/TypeScript) | tauri.app |
| Config management | `pydantic-settings` + `.env` | PyPI |
| Task scheduling | `APScheduler` | PyPI |

---

## ML/DL Models

### Primary SER Stack
| Model ID | Architecture | Training Data | Emotion Classes | Notes |
|----------|-------------|---------------|-----------------|-------|
| `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition` | wav2vec2-large-xlsr | RAVDESS, TESS | 8 classes (angry, calm, disgust, fearful, happy, neutral, sad, surprised) | Primary model |
| `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim` | wav2vec2-large | MSP-Podcast | Dimensional (valence, arousal, dominance) | Valence-arousal mapping |
| `speechbrain/emotion-recognition-wav2vec2-IEMOCAP` | wav2vec2 | IEMOCAP | 4 classes (angry, happy, neutral, sad) | Cross-validation / ensemble |

### Fine-Tuning Plan
- Base fine-tune `ehcalabres` model on user's own voice samples after 30+ interactions for personalized baseline calibration
- Training data: 10-second voice snippets collected with consent, labeled by user-confirmed ground truth mood
- Fine-tuning infrastructure: LoRA adapters on wav2vec2 feature extractor, ~50 samples sufficient for personalization
- Training frequency: Monthly re-calibration, triggered when accuracy drops below 70% (self-monitoring)

### Training Data Sources
- RAVDESS: https://zenodo.org/record/1188976
- IEMOCAP: https://sail.usc.edu/iemocap/
- MSP-Podcast: https://ecs.utdallas.edu/research/researchlabs/msp-lab/MSP-Podcast.html
- User-generated (opt-in, local only, never uploaded)

---

## External LLM API Integration

### Pluggable Backend Design
```python
class LLMBackend(Protocol):
    async def generate_mashup_spec(self, emotion_state: EmotionState, 
                                    user_profile: UserProfile) -> MashupSpec: ...

class ClaudeBackend(LLMBackend): ...   # uses CLAUDE_API_KEY
class GPT4Backend(LLMBackend): ...    # uses OPENAI_API_KEY  
class OllamaBackend(LLMBackend): ...  # uses OLLAMA_BASE_URL, no key needed
```

### Fallback Chain
1. Try Claude API (fastest, best reasoning)
2. If unavailable/rate-limited → fall back to GPT-4
3. If no internet or both APIs down → fall back to local Ollama (Mistral 7B)
4. If Ollama not installed → use rule-based template system (guaranteed offline operation)

### Prompt Design
The LLM receives a structured JSON context:
```json
{
  "emotion": {"valence": 0.3, "arousal": 0.7, "label": "anxious"},
  "mood_history": ["stressed", "anxious", "neutral"],
  "intervention_mode": "nudge",  // mirror | nudge | transform
  "user_preferences": {"genres": ["sci-fi", "drama"], "disliked": ["horror"]},
  "available_devices": ["spotify", "hue_lights", "tmdb"],
  "time_of_day": "evening",
  "session_duration_target": 90
}
```
And returns a structured `MashupSpec` JSON for downstream API calls.

---

## Feature Specification

### MVP Features
- [x] Voice capture + real-time SER inference (3-second rolling window)
- [x] Valence-arousal emotion mapping with confidence scoring
- [x] Spotify playlist generation based on mood (tempo, energy, valence parameters)
- [x] TMDB movie/show recommendation based on mood-mapped genre tags
- [x] LLM mashup orchestration (Claude/GPT-4/Ollama)
- [x] Basic smart lighting control (Philips Hue or Home Assistant)
- [x] SQLite mood history logging
- [x] Tauri desktop UI with mood dashboard and mashup card
- [x] Three intervention modes: mirror, nudge, transform

### Advanced Features
- [ ] Wearable biometric fusion (Garmin, Apple Watch, Fitbit)
- [ ] Multi-user mood aggregation (households, couples)
- [ ] Personalized SER fine-tuning from user's voice samples
- [ ] Aromatherapy diffuser integration (SwitchBot + custom BLE)
- [ ] Ambient sound layer (rain, forest, café — spa-style soundscapes)
- [ ] Circadian rhythm integration (adjust recommendations to time of day + sleep data)
- [ ] Mood trend analytics dashboard (weekly/monthly emotional patterns)
- [ ] "Mood journey" mode: 3-hour planned emotional arc toward a target state
- [ ] Smart TV integration (cast recommended content directly)
- [ ] Voice assistant integration (ask for mood report or manual override)
- [ ] Social sharing of mood-matched playlists (anonymous)
- [ ] Streaming service OAuth (Netflix via unofficial API, Amazon Prime)

---

## Full E2E Data Flow

1. **Audio Capture**: `sounddevice` records 3-second audio window from microphone at 16kHz
2. **Preprocessing**: `librosa` normalizes, removes silence, converts to mel spectrogram
3. **SER Inference**: wav2vec2 model runs locally → outputs emotion probabilities vector
4. **Biometric Fusion** (if wearable connected): BLE reads HRV/HR → normalized stress score → weighted fusion with SER output
5. **Emotion State Extraction**: Probabilities mapped to (valence, arousal) coordinates in Russell's circumplex model
6. **Mood History Update**: New state appended to SQLite `mood_history` table with timestamp
7. **Intervention Mode Selection**: Agent compares current state vs. user's target state / time-of-day defaults → selects mirror/nudge/transform mode
8. **LLM Orchestration Call**: Emotion state + user profile + history + intervention mode sent to Claude API (or fallback)
9. **Mashup Spec Returned**: LLM returns structured JSON: { film_query, spotify_seed_genres, spotify_tempo_range, hue_scene, diffuser_oils, narrative_message }
10. **Parallel API Calls**:
    - Spotify Web API: search playlists by seed genres, tempo, valence → return top 3 playlists
    - TMDB API: search movies/shows by genre IDs + mood keywords → return top 5 recommendations
    - Philips Hue API: activate named scene or set custom color temperature + brightness
    - SwitchBot API: schedule diffuser on/off cycle with selected oil profile
11. **Mashup Card Rendered**: Frontend displays combined card with movie poster, playlist preview, lighting preview swatch, diffuser suggestion, and LLM-generated narrative ("You seem tense — here's a calming evening curated for you")
12. **User Feedback**: Thumbs up/down, content rating, manual mood override → stored in SQLite for preference learning
13. **Continuous Loop**: System re-samples emotion every 5 minutes during active session, adjusts playlist/lighting in real-time if mood shifts significantly

---

## Privacy & Security

| Data Type | Processing Location | Storage | Encryption | Retention |
|-----------|-------------------|---------|-----------|-----------|
| Raw audio | Local (RAM only) | Never persisted | N/A (ephemeral) | 3 seconds |
| Emotion labels | Local | SQLite | AES-256-GCM | 90 days |
| Biometric data | Local | SQLite | AES-256-GCM | 90 days |
| User preferences | Local | SQLite | AES-256-GCM | Indefinite |
| Mashup history | Local | SQLite | AES-256-GCM | 1 year |
| API keys | Local | `.env` file | OS keychain | User-controlled |

**Principles:**
- Raw audio is never written to disk — only the emotion inference result (a probability vector) is persisted
- All LLM API calls include only anonymized emotion labels and preference tags — no voice data, no biometrics
- The system works fully offline (Ollama fallback) — no cloud dependency for core functionality
- GDPR-compliant: user can export or delete all personal data with one command

---

## Key Python/JS Dependencies

```
# Python backend
torch==2.3.0
transformers==4.41.0
sounddevice==0.4.7
librosa==0.10.2
spotipy==2.23.0
anthropic==0.28.0
openai==1.30.0
sqlalchemy==2.0.30
cryptography==42.0.8
phue==1.1
aiohttp==3.9.5
pydantic-settings==2.3.0
APScheduler==3.10.4
bleak==0.21.1

# Frontend (Tauri + React)
react: ^18.3.0
typescript: ^5.4.0
@tauri-apps/api: ^1.6.0
recharts: ^2.12.0        # mood trend charts
framer-motion: ^11.2.0   # UI animations
```

---

## Improvement Suggestions

1. **Facial expression fusion**: Add webcam-based FER (Facial Emotion Recognition) via `deepface` as a third sensing modality for higher accuracy multi-modal emotion detection
2. **Cross-device sync**: Allow multiple devices (phone, tablet, smart TV) to share the same active mashup session
3. **Mood-based content creation**: Instead of just recommending existing content, use an image generation model (Stable Diffusion) to generate custom wallpapers/ambience visuals matching the mood
4. **Therapist dashboard**: Aggregate long-term mood trends in a shareable PDF report for mental health practitioners
5. **A/B testing framework**: Systematically test which mashup bundles are most effective at shifting user mood toward target states, creating a self-improving recommendation engine
6. **Community mood pools**: Anonymous aggregate mood data from opt-in users to create "tonight's collective mood" playlists
7. **Predictive intervention**: Using time-series mood history, predict when the user is likely to enter a negative mood state and proactively stage the environment before the crash
8. **Physical world integration**: Connect to smart blinds, thermostat, and air purifier for full room-state orchestration beyond lighting
9. **Soundtrack mode**: Compose real-time adaptive background music using a generative music model (MusicGen) instead of pre-recorded playlists
10. **Sleep transition protocol**: Automatic 2-hour gradual wind-down program triggered by user's typical bedtime, progressively shifting lighting, music, and content toward sleep-inductive states
