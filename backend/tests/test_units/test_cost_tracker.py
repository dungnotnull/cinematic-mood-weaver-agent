"""Tests for LLM cost tracking and prompt cache."""

import tempfile
from pathlib import Path

from cinematic_mood_weaver.orchestration.cost_tracker import CostTracker, PromptCache


class TestCostTracker:
    def setup_method(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        self.log_path = Path(tmp.name)
        tmp.close()
        self.tracker = CostTracker(log_path=self.log_path)

    def teardown_method(self):
        self.log_path.unlink(missing_ok=True)

    def test_record_cost_claude(self):
        record = self.tracker.record("claude", input_tokens=1000, output_tokens=200)
        assert record.backend == "claude"
        assert record.cost_usd > 0
        assert record.cost_usd < 1.0
        assert self.tracker.today_cost() > 0

    def test_record_cost_ollama_free(self):
        record = self.tracker.record("ollama", input_tokens=5000, output_tokens=1000)
        assert record.cost_usd == 0.0

    def test_budget_remaining(self):
        assert self.tracker.budget_remaining() > 0
        assert self.tracker.over_budget() is False

    def test_log_file_created(self):
        assert self.log_path.exists()


class TestPromptCache:
    def setup_method(self):
        self.cache = PromptCache(max_size=3)

    def test_cache_miss(self):
        result = self.cache.get("nonexistent")
        assert result is None
        assert self.cache.hit_rate() == 0.0

    def test_cache_hit(self):
        self.cache.set("key1", "value1")
        result = self.cache.get("key1")
        assert result == "value1"
        assert self.cache.hit_rate() > 0.0

    def test_cache_eviction(self):
        self.cache.set("k1", "v1")
        self.cache.set("k2", "v2")
        self.cache.set("k3", "v3")
        self.cache.set("k4", "v4")  # Should evict k1
        assert self.cache.get("k1") is None
        assert self.cache.get("k4") == "v4"
