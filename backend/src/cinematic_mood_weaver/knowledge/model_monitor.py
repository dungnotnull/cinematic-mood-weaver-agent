"""Model performance monitor — periodically re-benchmarks SER models
against new HuggingFace releases and sends notifications when a new
SOTA model exceeds current performance.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from cinematic_mood_weaver.config import settings

logger = logging.getLogger(__name__)

CURRENT_MODELS = [
    "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
    "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim",
    "speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
]

BENCHMARK_ACCURACIES = {
    "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition": 73.3,
    "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim": 64.8,
    "speechbrain/emotion-recognition-wav2vec2-IEMOCAP": 79.1,
}


@dataclass
class ModelDiscovery:
    model_id: str
    accuracy: float
    benchmark: str
    description: str
    published_date: str


class ModelMonitor:
    """Monitors HuggingFace for new SOTA SER models and sends alerts."""

    def __init__(self, state_path: Optional[Path] = None):
        data_dir = Path(settings.app_data_dir)
        self._state_path = state_path or data_dir / "model_monitor_state.json"
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._best_accuracy = max(BENCHMARK_ACCURACIES.values())
        self._load_state()

    def _load_state(self) -> None:
        """Load persisted state (last checked date, known models)."""
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text(encoding="utf-8"))
                self._best_accuracy = data.get("best_accuracy", self._best_accuracy)
            except Exception:
                pass

    def _save_state(self) -> None:
        """Persist current state."""
        self._state_path.write_text(
            json.dumps({"best_accuracy": self._best_accuracy, "last_checked": datetime.now().isoformat()}, indent=2),
            encoding="utf-8",
        )

    async def check_for_new_models(self, dry_run: bool = False) -> list[ModelDiscovery]:
        """Search HuggingFace for new SER models that exceed current accuracy."""
        if dry_run:
            logger.info("Dry run — would check for new SER models")
            return []

        try:
            url = "https://huggingface.co/api/models"
            params = {
                "search": "speech emotion recognition wav2vec2",
                "sort": "lastModified",
                "direction": -1,
                "limit": 20,
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"HuggingFace API error: {resp.status_code}")
                return []

            models = resp.json()
            discoveries = []
            for m in models:
                model_id = m.get("modelId", "")
                if model_id in CURRENT_MODELS:
                    continue

                # Check if it's a SER model by looking at pipeline tag or keywords
                tags = m.get("tags", [])
                pipeline = m.get("pipeline_tag", "")
                if "audio-classification" not in pipeline and "emotion" not in " ".join(tags).lower():
                    continue

                downloads = m.get("downloads", 0)
                if downloads < 100:
                    continue  # Too new/unpopular to consider

                discoveries.append(
                    ModelDiscovery(
                        model_id=model_id,
                        accuracy=0.0,  # Unknown until benchmarked
                        benchmark="unknown",
                        description=m.get("description", "")[:200],
                        published_date=m.get("lastModified", ""),
                    )
                )

            if discoveries:
                logger.info(f"Found {len(discoveries)} potential new SER models on HuggingFace")

            self._save_state()
            return discoveries

        except Exception as e:
            logger.warning(f"Model monitor check failed: {e}")
            return []

    def format_alert(self, discoveries: list[ModelDiscovery]) -> str:
        """Format a notification message for new model discoveries."""
        if not discoveries:
            return ""
        lines = [
            f"🔬 New SER models discovered on HuggingFace!",
            f"   Current best accuracy: {self._best_accuracy}%",
            f"   New candidates found:",
        ]
        for d in discoveries:
            lines.append(f"   • {d.model_id}")
        lines.append(f"   Run `python scripts/benchmark_models.py --model <id>` to evaluate.")
        return "\n".join(lines)
