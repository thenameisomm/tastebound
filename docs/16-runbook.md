# 16. Runbook

## Prerequisites

Node and pnpm (as in the repo), Python 3.12 and `uv`, Supabase CLI (Docker optional for local Supabase), and keys: Qloo hackathon key, Ollama Cloud key, Supabase project(s).

## First-time setup

```bash
pnpm install
(cd apps/api && uv sync)

supabase init                                  # if supabase/ is missing
supabase migration new init                    # paste 0001 SQL from docs/06
supabase start && supabase db reset            # local (Docker)
# or: supabase link --project-ref <dev-ref> && supabase db push

cp apps/api/.env.example apps/api/.env         # fill values (docs/03)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > apps/web/.env.local

(cd apps/api && uv run python scripts/load_markets.py)   # loads data/markets.json into the markets table
pnpm turbo dev                                 # web :3000, api :8000
curl -s localhost:8000/health
```

`apps/api/package.json`:

```json
{
  "name": "api",
  "private": true,
  "scripts": {
    "dev": "uv run uvicorn tastebound_api.main:app --reload --port 8000",
    "lint": "uv run ruff check . && uv run ruff format --check . && uv run mypy src",
    "test": "uv run pytest -m \"not live\"",
    "build": "uv run python scripts/export_openapi.py"
  }
}
```

## Phase 0

```bash
cd apps/api
uv run python scripts/spike_qloo.py --destinations "Lisbon,PT;Kyoto,JP" --markets preset:europe20,preset:na15,preset:apac15 --out tests/fixtures/qloo/
uv run python scripts/spike_llm_tools.py
```

## Seed demo and evaluate

```bash
uv run python scripts/seed_demo.py --destination "<name>,<CC>" --arrivals src/tastebound_api/data/samples/<file>.csv --shortlist 5 --budget 250000
uv run python scripts/evaluate.py --destinations <id1>,<id2> --markets preset:europe20,preset:na15 --out ../../docs/evaluation-results.md
```

## Useful SQL

```sql
select count(*) from qloo_calls where cache_hit = false and created_at > now() - interval '30 days';
select run_id, count(*) filter (where not cache_hit) live, count(*) filter (where cache_hit) cached
from qloo_calls group by run_id order by max(created_at) desc limit 10;
```

## Deploy

| Part | Where | Notes |
|---|---|---|
| DB | Supabase Cloud (prod project) | `supabase link --project-ref <prod>`, `supabase db push`, load markets |
| API | Render / Railway / Fly.io, **one instance** | `uv run uvicorn tastebound_api.main:app --host 0.0.0.0 --port $PORT`; all env vars; in-process rate limiters |
| Web | Vercel, root `apps/web` | `NEXT_PUBLIC_API_URL` = API URL; add web origin to `CORS_ORIGINS` |

Then seed the demo in production, set `DEMO_RUN_ID`, test `/sample` in a private window, and run one live run.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `prepared statement ... does not exist` | Transaction pooler + asyncpg cache | `statement_cache_size=0` or direct/session connection |
| Qloo 401 | Key/header/base URL | Check `QLOO_API_KEY`, `X-Api-Key`, `QLOO_BASE_URL` |
| Market results identical for every market | Location parameter ignored (silent 200) | Re-check `docs/qloo-contract.md`; guards should warn |
| Most non-US markets empty | Coverage | Switch strategy, enlarge radius, drop thin markets, state the limit |
| Ollama 401/404 | Key or model name | Fix `OLLAMA_API_KEY`; pick a name from `/api/tags` |
| Model replies with text, not tools | Tool calling unsupported/unstable | Planner or deterministic fallback runs; check `docs/llm-contract.md` |
| CORS error | Missing origin | Add to `CORS_ORIGINS` |
| Empty `/sample` | `DEMO_RUN_ID` unset or wrong DB | Seed and set it |
