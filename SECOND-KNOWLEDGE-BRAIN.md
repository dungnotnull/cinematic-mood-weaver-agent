# SECOND-KNOWLEDGE-BRAIN.md — cinematic-mood-weaver-agent

## Overview
This is the self-improving knowledge base for the cinematic-mood-weaver-agent project. It is automatically updated by a weekly crawler targeting affective computing, speech emotion recognition, and multi-sensory experience research. New entries are always date-stamped and appended to preserve a full knowledge history.

---

## Core Concepts & Theoretical Foundations

### 1. Affective Computing
Introduced by Rosalind Picard (MIT Media Lab, 1997) — the field of computing that recognizes, interprets, and simulates human emotions. The foundational premise: machines that can sense and respond to emotional states will fundamentally improve human-computer interaction. Three pillars relevant to this project:
- **Emotion sensing**: Physiological signals (HRV, EDA), vocal features (SER), facial expressions (FER)
- **Emotion representation**: Discrete labels (Ekman's 6 basic emotions) vs. dimensional models (Russell's circumplex)
- **Emotion response**: Adaptive systems that change behavior based on detected state

### 2. Russell's Circumplex Model of Affect
The standard 2D representation of emotional states:
- **Valence axis** (X): Negative (−1) to Positive (+1) — how pleasant/unpleasant
- **Arousal axis** (Y): Low (−1) to High (+1) — how activated/deactivated
- Key emotion coordinates: Happy = high valence + high arousal; Sad = low valence + low arousal; Anxious = low valence + high arousal; Calm = high valence + low arousal
- Practical use: Spotify's audio features map to this space (valence + energy parameters)

### 3. Speech Emotion Recognition (SER)
The task of identifying emotional states from speech signals independent of linguistic content. Key technical approaches:
- **Handcrafted feature methods**: MFCC, mel spectrogram, pitch contour, speech rate → classical ML classifiers
- **End-to-end deep learning**: CNN/RNN/Transformer directly on raw waveform or spectrogram
- **Self-supervised pre-training**: wav2vec2, HuBERT, WavLM pre-trained on unlabeled speech → fine-tuned on emotion labels
- The wav2vec2 paradigm has dominated since 2021, achieving near-human accuracy on benchmark datasets

### 4. Heart Rate Variability (HRV) as Stress Proxy
HRV measures variation in time intervals between consecutive heartbeats (RR intervals). Key metrics:
- **RMSSD**: Root Mean Square of Successive RR Differences — primary parasympathetic activity measure
- **SDNN**: Standard deviation of NN intervals — overall autonomic nervous system activity
- **LF/HF ratio**: Low-frequency to high-frequency power ratio — sympathetic/parasympathetic balance
- Low HRV correlates strongly with high stress, anxiety, and negative emotional states
- Wearables (Garmin, Apple Watch, Polar H10) provide real-time HRV data via BLE or SDK

### 5. Mood Congruence Effect in Media Consumption
Psychological principle: people in negative moods tend to choose mood-congruent media (sad music when sad), while positive moods lead to mood-incongruent seeking (upbeat content to maintain positivity). Implications:
- Recommendation systems should distinguish between "mirror current mood" vs. "guide toward target mood" strategies
- Context matters: a user who wants to process sadness benefits from congruent content; one who wants to escape benefits from incongruent
- This is the basis for the three intervention modes: mirror / nudge / transform

### 6. Multi-Sensory Emotion Regulation
Research on environmental psychology demonstrates that simultaneous multi-channel sensory stimulation (visual, auditory, olfactory, thermal) produces stronger emotional regulation effects than any single channel alone:
- **Color psychology**: Warm colors (amber, red) increase arousal; cool colors (blue, green) decrease arousal
- **Aromatherapy**: Lavender reduces cortisol; citrus increases alertness; peppermint improves focus
- **Music tempo and BPM**: >140 BPM energizing; <80 BPM calming; minor keys sad-signaling
- **Luminance**: Bright light increases alertness and positive affect; dim light reduces stress

---

## Key Research Papers

| Title | Authors | Year | Venue | DOI / Link | Relevance |
|-------|---------|------|-------|-----------|-----------|
| Affective Computing | R. Picard | 1997 | MIT Press | ISBN: 0-262-16170-7 | Foundational text for the entire field |
| A Circumplex Model of Affect | J.A. Russell | 1980 | J. of Personality and Social Psychology | doi:10.1037/h0077714 | Valence-arousal 2D emotion space model used for mapping |
| wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations | Baevski et al. | 2020 | NeurIPS | arXiv:2006.11477 | Core architecture of the SER models used |
| Emotion Recognition in Conversations: Research and Challenges | Poria et al. | 2019 | arXiv | arXiv:1905.02947 | Multi-modal emotion detection framework |
| Speech Emotion Recognition Using Deep Learning Techniques | Kwon | 2021 | IEEE Access | doi:10.1109/ACCESS.2021.3101891 | Benchmarks for DL-based SER systems |
| Dimensional Emotion Recognition from Speech Using wav2vec 2.0 | Wagner et al. | 2023 | INTERSPEECH | arXiv:2203.07378 | audeering model — predicts valence/arousal continuously |
| HRV Biofeedback for Emotion Regulation | Gevirtz | 2013 | Biofeedback | doi:10.5298/1081-5937-41.3.01 | HRV as real-time stress/emotion biomarker |
| Mood Congruence in Media Selection | Knobloch & Zillmann | 2002 | Personality and Social Psychology Bulletin | doi:10.1177/014616720202800204 | Theoretical basis for mood-matching recommendation |
| Affective Responses to Music: The Need to Consider Underlying Mechanisms | Juslin & Vastfjall | 2008 | Behavioral and Brain Sciences | doi:10.1017/S0140525X08005293 | Music-emotion mapping mechanisms |
| Music and Emotion: Toward New Theoretical Perspectives | Scherer | 2004 | Cambridge Handbook of Music Psychology | ISBN: 978-0521889209 | Categorical and dimensional emotion-music mapping |
| The Psychophysiology of Real-Life Emotion | Mauss & Robinson | 2009 | Social and Personality Psychology Compass | doi:10.1111/j.1751-9004.2009.00244.x | Multi-signal physiological emotion detection |
| A Survey on Multimodal Sentiment Analysis | Soleymani et al. | 2017 | IEEE Transactions on Affective Computing | doi:10.1109/TAFFC.2017.2736661 | Multimodal fusion methods for emotion detection |
| Personalizing Emotion Recognition: User Adaptation in Affective Computing | Kessous et al. | 2010 | Cognitive Computation | doi:10.1007/s12559-010-9064-7 | Personalized calibration for SER systems |

---

## State-of-the-Art ML/DL Models

### Speech Emotion Recognition

| Model ID (HuggingFace) | Architecture | Benchmark | Accuracy | Use Case |
|------------------------|-------------|-----------|----------|---------|
| `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition` | wav2vec2-large-xlsr | RAVDESS | 73.3% | Primary 8-class SER |
| `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim` | wav2vec2-large | MSP-Podcast | CCC: 0.638 (valence) | Dimensional valence/arousal output |
| `speechbrain/emotion-recognition-wav2vec2-IEMOCAP` | wav2vec2 + ECAPA | IEMOCAP | 79.1% (4-class) | Ensemble cross-validation |
| `jonatasgrosman/wav2vec2-large-xlsr-53-english` | wav2vec2-large-xlsr-53 | — | — | Feature extractor base |
| `facebook/hubert-large-ls960-ft` | HuBERT large | — | — | Alternative feature extractor |

### Multimodal Emotion Recognition

| Model / Framework | Modalities | Benchmark | Notes |
|-------------------|-----------|-----------|-------|
| MulT (Multimodal Transformer) | Audio + Text + Video | CMU-MOSI | 84.3% | arXiv:1906.00295 |
| MMSA | Audio + Video | IEMOCAP | 82.1% | Multi-task learning approach |
| EmoBERTa | Text only | IEMOCAP | 75.3% | Text fallback when voice unavailable |

### Generative Models (Advanced Features)

| Model | Purpose | HuggingFace ID |
|-------|---------|---------------|
| MusicGen (Meta) | Real-time mood-matched music generation | `facebook/musicgen-small` |
| Stable Diffusion XL | Mood-matched ambient wallpaper generation | `stabilityai/stable-diffusion-xl-base-1.0` |
| LLaMA 3 8B | Local LLM for mashup orchestration | `meta-llama/Meta-Llama-3-8B-Instruct` |

---

## Tools, Libraries & Frameworks

| Tool | Purpose | Link | Notes |
|------|---------|------|-------|
| HuggingFace Transformers | SER model inference | https://github.com/huggingface/transformers | Core ML inference library |
| sounddevice | Real-time audio capture from microphone | https://github.com/spatialaudio/python-sounddevice | Low-latency audio streaming |
| librosa | Audio feature extraction (MFCC, mel spectrogram) | https://github.com/librosa/librosa | Preprocessing pipeline |
| spotipy | Spotify Web API Python client | https://github.com/spotipy-dev/spotipy | Playlist discovery + generation |
| tmdbsimple | TMDB API Python wrapper | https://github.com/celiao/tmdbsimple | Movie/TV recommendation |
| phue | Philips Hue API Python client | https://github.com/studioimaginaire/phue | Smart lighting control |
| bleak | BLE (Bluetooth Low Energy) async library | https://github.com/hbldh/bleak | Wearable biometric data reading |
| anthropic | Claude API Python SDK | https://github.com/anthropics/anthropic-sdk-python | Primary LLM orchestration |
| ollama | Local LLM client | https://github.com/ollama/ollama | Offline fallback LLM |
| crawl4ai | AI-powered web crawler | https://github.com/unclecode/crawl4ai | SECOND-KNOWLEDGE-BRAIN auto-updater |
| SQLAlchemy | Python ORM for SQLite | https://github.com/sqlalchemy/sqlalchemy | Mood history + preferences storage |
| cryptography | AES-256-GCM encryption | https://github.com/pyca/cryptography | Local data privacy |
| Tauri | Desktop app framework (Rust + web frontend) | https://github.com/tauri-apps/tauri | Cross-platform desktop UI |
| Recharts | React charting library | https://github.com/recharts/recharts | Valence-arousal mood dashboard |
| APScheduler | Python task scheduler | https://github.com/agronholm/apscheduler | Periodic mood sampling, knowledge updates |
| Home Assistant | Smart home hub | https://github.com/home-assistant/core | Universal smart device control alternative to Hue SDK |

---

## Self-Update Protocol

### Crawler Configuration (crawl4ai)

**Target Sources:**
| Source | URL / Query | Category |
|--------|------------|---------|
| ArXiv cs.HC | https://arxiv.org/search/?query=emotion+recognition&searchtype=all&start=0 | Affective computing papers |
| ArXiv cs.SD | https://arxiv.org/search/?query=speech+emotion+recognition&searchtype=all | SER papers |
| ArXiv cs.AI | https://arxiv.org/search/?query=mood+recommendation+system&searchtype=all | Recommendation systems |
| HuggingFace Papers | https://huggingface.co/papers?q=speech+emotion+recognition | ML model releases |
| ACM Digital Library | https://dl.acm.org/action/doSearch?query=affective+computing+recommendation | Affective computing research |
| IEEE Xplore | https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=speech+emotion+recognition | Engineering papers |
| Google Scholar | https://scholar.google.com/scholar?q=real-time+emotion+recognition+wearable | Wearable emotion sensing |
| Papers with Code | https://paperswithcode.com/task/speech-emotion-recognition | SOTA benchmarks |

**Domain-Specific Search Queries:**
```
speech emotion recognition 2024 2025
affective computing recommendation system
real-time emotion detection wearable
HRV heart rate variability emotion prediction
multimodal emotion recognition audio visual
mood-based content recommendation
wav2vec2 emotion fine-tuning
biometric emotion fusion
smart home emotion responsive
personalized emotion recognition adaptation
```

**Update Frequency:** Weekly (every Monday at 06:00 local time)

**crawl4ai Configuration:**
```python
from crawl4ai import AsyncWebCrawler

KNOWLEDGE_BRAIN_SOURCES = [
    {
        "name": "arxiv_ser",
        "url": "https://arxiv.org/search/?query=speech+emotion+recognition&searchtype=all&order=-announced_date_first",
        "selectors": {"title": ".title", "authors": ".authors", "abstract": ".abstract", "link": ".title a"},
        "relevance_keywords": ["emotion", "speech", "affective", "recognition", "mood"],
        "max_results_per_run": 10
    },
    {
        "name": "huggingface_papers",
        "url": "https://huggingface.co/papers?q=emotion+recognition",
        "selectors": {"title": "h3", "abstract": "p.abstract"},
        "relevance_keywords": ["emotion", "speech", "sentiment", "affect"],
        "max_results_per_run": 5
    }
]

LLM_RELEVANCE_FILTER_PROMPT = """
Given this paper abstract, rate its relevance (0-10) to a project that:
1. Does real-time speech emotion recognition
2. Uses biometric data (HRV, heart rate) for emotion detection
3. Recommends movies, music, and smart home environments based on mood
4. Uses transformer-based models (wav2vec2 family)

Return JSON: {"relevance_score": int, "reason": str, "key_contribution": str}
Paper abstract: {abstract}
"""
```

**Format for New Entries:**
```markdown
### [DATE: YYYY-MM-DD] Title of Paper
- **Authors:** Last, F. et al.
- **Year:** YYYY
- **Venue:** Conference/Journal Name
- **Link:** https://arxiv.org/abs/XXXX.XXXXX
- **Relevance:** Why this matters to cinematic-mood-weaver-agent (1-2 sentences)
- **Key Contribution:** The main technical advance
- **Action Required:** [New model to evaluate / New technique to implement / Background reading]
```

---

## Knowledge Update Log

### [2026-06-03] Initial Knowledge Base Population
- **Added:** 13 foundational research papers on affective computing, SER, HRV, and mood-based recommendation
- **Added:** 5 primary HuggingFace SER models with benchmarks
- **Added:** 2 advanced generative models (MusicGen, Stable Diffusion XL) for future features
- **Added:** 15 core tools and libraries with GitHub links
- **Added:** Theoretical foundations: Russell's circumplex model, affective computing, SER, HRV, mood congruence, multi-sensory regulation
- **Status:** Crawler not yet deployed (Phase 4, Week 13-14)
- **Next Update:** 2026-06-10 (once crawler is operational)

---

## Domain Glossary

| Term | Definition |
|------|-----------|
| SER | Speech Emotion Recognition — identifying emotions from voice signals |
| HRV | Heart Rate Variability — variation in time between heartbeats; proxy for stress level |
| EDA | Electrodermal Activity (galvanic skin response) — skin conductance measure of arousal |
| Valence | The pleasantness dimension of emotion (-1 = very negative, +1 = very positive) |
| Arousal | The activation/energy dimension of emotion (-1 = very calm, +1 = very excited) |
| FER | Facial Expression Recognition — detecting emotions from face images/video |
| MFCC | Mel-Frequency Cepstral Coefficients — handcrafted audio feature for voice analysis |
| CCC | Concordance Correlation Coefficient — metric for continuous emotion prediction (valence/arousal) |
| RAVDESS | Ryerson Audio-Visual Database of Emotional Speech and Song — SER benchmark dataset |
| IEMOCAP | Interactive Emotional Dyadic Motion Capture — 12-hour acted conversation emotion dataset |
| MSP-Podcast | Podcast-based naturalistic speech emotion dataset from UT Dallas |
| BLE | Bluetooth Low Energy — wireless protocol used by wearables to stream biometric data |
| LoRA | Low-Rank Adaptation — parameter-efficient fine-tuning technique for large models |
| Mashup | In this project: a synchronized bundle of film + music + lighting + diffuser recommendations |
| Mirror mode | Intervention mode where recommendations match the user's current emotional state |
| Nudge mode | Intervention mode that gently guides the user toward a more positive emotional state |
| Transform mode | Intervention mode that strongly redirects the user toward a target emotional state |
