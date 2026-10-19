# TasteBound API

FastAPI service for TasteBound. Qloo decides taste; the LLM narrates.

```bash
uv sync
uv run uvicorn tastebound_api.main:app --reload --port 8000
uv run pytest -m "not live"
```

Configuration lives in `.env` (see `.env.example`). The API fails closed when Qloo is not configured.
