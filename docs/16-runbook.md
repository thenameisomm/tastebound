# 16. Runbook

## Prerequisites

- Node.js 24+ and pnpm (the repo pins pnpm 11.25.0)
- Python 3.12 or 3.13 and `uv`
- A Qloo hackathon key for live runs
- Optional: an Ollama Cloud key for item suggestions, gated model-written briefs and the read-only results assistant
- Optional: `pnpm exec playwright install chromium` for screenshot, smoke and axe scripts

## Local setup

```bash
pnpm install
(cd apps/api && uv sync)

cp apps/api/.env.example apps/api/.env
chmod 600 apps/api/.env
# Fill QLOO_API_KEY. OLLAMA_API_KEY is optional.

echo "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000" > apps/web/.env.local

pnpm turbo dev
```

| Service  | URL                          |
| -------- | ---------------------------- |
| Web      | http://localhost:3000        |
| API      | http://127.0.0.1:8000        |
| API docs | http://127.0.0.1:8000/docs   |
| Health   | http://127.0.0.1:8000/health |

On first boot the API creates the SQLite schema, loads the 68-market catalogue and seeds the read-only Lisbon demo from `apps/api/data/demo/lisbon-run.json`.

Open `/sample` to use the keyless demo. A live run starts at `/start`.

## Demo fixture

The demo is exported from a completed local run and stored in git:

```bash
cd apps/api
uv run python scripts/export_demo.py <run_id> --output data/demo/lisbon-run.json
```

Restart the API after replacing the fixture. The startup seed deletes and re-inserts the same demo run ID, so the sample remains read-only for non-demo workspaces. `data/demo/active.json` is a local pointer to the seeded run and is not committed.

To reset local state completely, stop the API, remove `apps/api/data/tastebound.db`, and start the API again. It recreates the schema, market catalogue and demo.

## Phase 0 spike

The original Qloo verification script is retained:

```bash
cd apps/api
uv run python scripts/spike_phase0.py
```

It spends real Qloo calls and requires `QLOO_API_KEY`. Recorded findings live in `docs/qloo-contract.md`; do not treat the script as a test.

## Checks

```bash
(cd apps/api && uv run ruff check . && uv run ruff format --check . && uv run mypy src)
(cd apps/api && uv run pytest -m "not live")       # no network
pnpm test                                           # API + web tests, no network
pnpm turbo lint check-types build

# With both servers running:
node scripts/smoke-web.mjs
node scripts/a11y-check.mjs
```

Live Qloo checks are opt-in and never run in CI: `(cd apps/api && uv run pytest -m live)`.

Assistant conversations are not in SQLite. Restarting the API clears them; the web app clears a stale `sessionStorage` pointer after a 404. To test the assistant locally without a real model, use the fake provider from the test suite rather than a production env switch.

If a schema or route changes, export the OpenAPI document and regenerate the TypeScript contracts:

```bash
(cd apps/api && uv run python scripts/export_openapi.py)
pnpm --filter @repo/contracts generate
```

## Useful SQL

SQLite:

```bash
sqlite3 apps/api/data/tastebound.db \
  "select count(*) from qloo_calls where cache_hit = 0 and created_at > datetime('now','-30 days');"
```

Postgres/Supabase:

```sql
select count(*) from qloo_calls where cache_hit = false and created_at > now() - interval '30 days';

select run_id,
       count(*) filter (where not cache_hit) as live,
       count(*) filter (where cache_hit) as cached
from qloo_calls
group by run_id
order by max(created_at) desc
limit 10;
```

## Deploy

| Part     | Where                                       | Notes                                                                                                                                         |
| -------- | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Database | Supabase Cloud (optional)                   | Set `DATABASE_URL`; create the schema through `init_db` or your own migrations, then seed the demo                                            |
| API      | Render / Railway / Fly.io, **one instance** | `uv run uvicorn tastebound_api.main:app --host 0.0.0.0 --port $PORT`; all secrets as server-side env vars; in-process rate limits and budgets |
| Web      | Vercel, root `apps/web`                     | `NEXT_PUBLIC_API_URL` = API URL; add the web origin to `CORS_ORIGINS`                                                                         |

After deploying, open `/sample` in a private window, start one live run, and confirm `/health`. For a production deployment, add versioned migrations and backups first.

## Troubleshooting

| Symptom                                      | Cause                                                                | Fix                                                                                             |
| -------------------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `prepared statement ... does not exist`      | Transaction pooler + asyncpg                                         | Use a direct/session connection; the engine already sets `statement_cache_size=0`               |
| Qloo 401                                     | Key, header or base URL                                              | Check `QLOO_API_KEY`, the `X-Api-Key` header and `QLOO_BASE_URL=https://hackathon.api.qloo.com` |
| Market results identical for every market    | Location parameter ignored (silent 200)                              | Re-check `docs/qloo-contract.md`; guards should warn                                            |
| Most non-US markets empty                    | Coverage                                                             | Switch strategy, enlarge radius, drop thin markets and state the limit                          |
| Ollama 401/404                               | Key or model name                                                    | Fix `OLLAMA_API_KEY`; choose a name available in the account's Ollama library                   |
| Briefs say `template`                        | LLM unavailable, quota exhausted, or grounding rejected the output   | Expected fallback; check `/health` and the trace                                                |
| Assistant says “No model configured”         | `OLLAMA_API_KEY` missing or provider construction failed             | Add the key and restart the API; the rest of the app is unaffected                              |
| Assistant says it could not verify an answer | Model output had an unknown number/name/evidence ID after one repair | Rephrase or ask a narrower question; check the provider model, not the run scores               |
| Assistant rate-limited                       | 30/hour/IP or 60/hour/workspace reached                              | Wait for the window to pass; limits are in-process and reset on restart                         |
| Conversation disappeared                     | TTL expired or API restarted                                         | Expected; conversations are not durable                                                         |
| CORS error                                   | Missing origin                                                       | Add the web origin to `CORS_ORIGINS`                                                            |
| Empty `/sample`                              | Demo fixture missing or seed failed                                  | Confirm `apps/api/data/demo/lisbon-run.json` exists and restart the API                         |
| `database is locked`                         | Concurrent SQLite writers                                            | WAL and a 30 s timeout are configured; run one API instance                                     |
