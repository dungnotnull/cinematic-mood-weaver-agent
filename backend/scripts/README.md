# Phase 0b — Setup & Verification Scripts

Run once when setting up the project for the first time. All scripts support `--dry-run` to preview without side effects.

## Quick Start

```bash
# Full setup (recommended — runs everything)
python scripts/setup.py

# Or run individual steps:
python scripts/setup_env.py              # Create venv + install deps
python scripts/credentials_setup.py       # Configure API keys interactively
python scripts/download_models.py         # Download SER models
python scripts/benchmark_models.py        # Benchmarks
python scripts/smoke_test.py              # Verify all connections
python scripts/verify_health.py           # Full system health check + demo
```

## Step Details

| Script | What It Does | Dry Run? |
|--------|-------------|----------|
| `setup_env.py` | Creates `.venv`, installs deps, creates app data dir | ✓ |
| `credentials_setup.py` | Interactive wizard for all API keys → writes `.env` | ✓ |
| `download_models.py` | Downloads 3 SER models from HuggingFace | ✓ |
| `benchmark_models.py` | Measures inference latency on CPU/CUDA | ✓ |
| `smoke_test.py` | Tests each API endpoint for connectivity | ✓ |
| `verify_health.py` | Comprehensive health check + demo cycle | ✓ |
| `setup.py` | Master orchestrator — runs all of the above | ✓ |
