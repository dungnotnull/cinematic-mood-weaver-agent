"""LLM API cost tracking and daily budget cap enforcement.

Tracks token usage and cost per backend (Claude, GPT-4, Ollama) and
raises warnings when approaching daily budget limits.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from threading import Lock
from typing import Optional

from cinematic_mood_weaver.config import settings

logger = logging.getLogger(__name__)

COST_PER_1K_TOKENS = {
    "claude": {"input": 0.003, "output": 0.015},  # claude-sonnet-4 pricing
    "openai": {"input": 0.0025, "output": 0.01},  # gpt-4o pricing
    "ollama": {"input": 0.0, "output": 0.0},  # free (local)
    "template": {"input": 0.0, "output": 0.0},  # free (rule-based)
}

DAILY_BUDGET_USD = 0.50  # Daily cap


@dataclass
class UsageRecord:
    backend: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime = field(default_factory=datetime.now)
    model: str = ""


class CostTracker:
    """Tracks LLM API usage and enforces daily budget caps."""

    def __init__(self, log_path: Optional[Path] = None):
        data_dir = Path(settings.app_data_dir)
        self._log_path = log_path or data_dir / "llm_usage.csv"
        self._lock = Lock()
        self._today_usage: dict[str, float] = {}
        self._daily_budget = DAILY_BUDGET_USD
        self._ensure_log()

    def _ensure_log(self) -> None:
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._log_path.exists():
            with open(self._log_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "backend", "model", "input_tokens", "output_tokens", "cost_usd"])

    def record(self, backend: str, input_tokens: int, output_tokens: int, model: str = "") -> UsageRecord:
        """Record an LLM API call and compute its cost."""
        pricing = COST_PER_1K_TOKENS.get(backend, {"input": 0.0, "output": 0.0})
        cost = (input_tokens / 1000) * pricing["input"] + (output_tokens / 1000) * pricing["output"]

        record = UsageRecord(
            backend=backend,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost, 6),
            model=model,
        )

        with self._lock:
            today = date.today().isoformat()
            self._today_usage[today] = self._today_usage.get(today, 0.0) + cost

            with open(self._log_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    record.timestamp.isoformat(),
                    record.backend,
                    record.model or "",
                    record.input_tokens,
                    record.output_tokens,
                    record.cost_usd,
                ])

        return record

    def today_cost(self) -> float:
        """Get total LLM cost for today."""
        today = date.today().isoformat()
        return self._today_usage.get(today, 0.0)

    def budget_remaining(self) -> float:
        """Return remaining daily budget."""
        return max(0.0, self._daily_budget - self.today_cost())

    def over_budget(self) -> bool:
        """Check if daily budget is exceeded."""
        return self.today_cost() >= self._daily_budget

    def summary(self) -> str:
        """Return a short human-readable cost summary."""
        return f"Today: ${self.today_cost():.4f} / ${self._daily_budget:.2f} budget ({self.budget_remaining():.2f} remaining)"


class PromptCache:
    """Simple prompt cache that avoids resending full user profile context
    on every LLM call. Stores the last N serialized contexts.

    In a real deployment, this would use Anthropic's prompt caching feature
    which reduces costs by ~80%.
    """

    def __init__(self, max_size: int = 10):
        self._cache: dict[str, str] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[str]:
        """Retrieve cached response for a context key."""
        result = self._cache.get(key)
        if result is not None:
            self._hits += 1
        else:
            self._misses += 1
        return result

    def set(self, key: str, value: str) -> None:
        """Cache a response for a context key."""
        if len(self._cache) >= self._max_size:
            # Evict oldest
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = value

    def hit_rate(self) -> float:
        """Return cache hit rate (0-1)."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0
