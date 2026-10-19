# 19. Setup: keys and running TasteBound

Verified against the repository on 2026-10-19. Local mode needs **no Docker, no Supabase account and no LLM key**: SQLite, the 68-market catalogue and the read-only Lisbon sample are created on first boot.

## 1. Prerequisites

| Tool | Version | Check |
|---|---|---|
| Node.js | ≥ 24 | `node -v` |
| pnpm | 11.x (repo pins 11.25.0) | `pnpm -v` |
| Python | 3.12 or 3.13 | `python3 --version` |
| uv | latest | `uv --version` |

Optional for the verification scripts: `pnpm exec playwright install chromium`.

## 2. Keys: what is needed and where to put it

All keys live in **`apps/api/.env`** (server-side only). Copy the template and never commit the result:

```bash
cp apps/api/.env.example apps/api/.env
chmod 600 apps/api/.env
```

| Variable | Required? | What it does | How to get it |
|---|---|---|---|
| `QLOO_API_KEY` | **Yes for live runs** | Authenticates every Qloo call (`X-Api-Key`). Without it the app boots, the sample works, and live runs fail closed with `qloo_unconfigured` | Qloo Agentic Hackathon dashboard/resources (https://qloo.devpost.com) |
| `OLLAMA_API_KEY` | Optional | Gemma 4 on Ollama Cloud: proposes signature items and writes grounded briefs. Without it runs still complete with deterministic tools and briefs labelled `template` | https://ollama.com → account → API keys |
| `SESSION_SECRET` | Change for deployment | Signs workspace tokens; the default is for local development only | `openssl rand -hex 32` |
| `DATABASE_URL` | Optional | Postgres/Supabase DSN. Empty = local SQLite at `apps/api/data/tastebound.db` | Supabase project → Database → connection string |
| `CORS_ORIGINS` | Change for deployment | Comma-separated browser origins allowed to call the API | e.g. `https://your-web.vercel.app` |

The browser never receives any key. The Next.js app only knows `NEXT_PUBLIC_API_URL`, and every Qloo/Ollama call happens in the API.

### Postgres / Supabase instead of SQLite

```dotenv
DATABASE_URL=postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres
```

- `postgresql://` and `postgres://` are rewritten to `postgresql+asyncpg://` automatically.
- Use a **direct or session** connection, not the transaction pooler. The engine already sets `statement_cache_size=0` for Postgres, but the pooler's prepared-statement behaviour is the most common failure (`prepared statement ... does not exist`).
- Tables and the market catalogue are created automatically at startup (`init_db`), then the demo fixture is seeded if present.

### Optional tuning (defaults are fine)

| Variable | Default | Purpose |
|---|---|---|
| `QLOO_RPS` | `4` | Request spacing; keep ≤ 4 for the hackathon key |
| `QLOO_MAX_CALLS_PER_RUN` | `200` | Per-run live-call budget |
| `QLOO_MONTHLY_CALL_LIMIT` | `10000` | Monthly guard (stops at 80%) |
| `QLOO_CACHE_TTL_HOURS` | `168` | Qloo response cache TTL |
| `MAX_MARKETS_PER_RUN` | `40` | Hard cap on selected origin markets |
| `MAX_SIGNATURE_ITEMS` | `15` | Cap on destination items |
| `PUBLIC_RUNS_PER_IP_PER_DAY` | `30` | Abuse limit on run creation |
| `OLLAMA_MODEL` | `gemma4:31b-cloud` | Model name on Ollama Cloud |
| `LLM_PROVIDER` | `ollama_cloud` | Provider adapter; this project uses Ollama only |
| `LLM_TOOL_CALLING` | `false` | Tool-choice loop switch; keep false until live tool calling is verified |

Do not add OpenRouter or another gateway, and do not put any key in a `NEXT_PUBLIC_*` variable.

## 3. Run the whole app (local, SQLite)

```bash
pnpm install
(cd apps/api && uv sync)

cp apps/api/.env.example apps/api/.env      # then edit QLOO_API_KEY / OLLAMA_API_KEY
chmod 600 apps/api/.env

echo "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000" > apps/web/.env.local

pnpm turbo dev
```

| Service | URL |
|---|---|
| Web | http://localhost:3000 |
| API | http://127.0.0.1:8000 |
| API docs | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/health |

On first boot the API creates the SQLite tables, loads the 68-market catalogue and seeds the read-only Lisbon demo. The first request may take a few seconds while this finishes.

### Verify

1. `curl -s http://127.0.0.1:8000/health` → `status: ok`; `qloo` is `configured` or `unconfigured`; `llm.tools_ok` stays `false` while `LLM_TOOL_CALLING=false`.
2. Open http://localhost:3000/sample — keyless, read-only, spends no Qloo quota.
3. Open http://localhost:3000/start — create a destination, resolve the profile, pick 20–40 markets, optionally upload arrivals or use the bundled sample, then start a run. The Qloo counter and trace update live.
4. Open http://localhost:3000/docs (API) to inspect endpoints.

### Run the services separately

```bash
# API
(cd apps/api && uv run uvicorn tastebound_api.main:app --reload --port 8000)

# Web (separate terminal)
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 pnpm --filter web dev
```

If port 8000 is already in use, run the API on another port and point the web app at it:

```bash
(cd apps/api && uv run uvicorn tastebound_api.main:app --reload --port 8020)
NEXT_PUBLIC_API_URL=http://127.0.0.1:8020 pnpm --filter web dev
```

`NEXT_PUBLIC_API_URL` is inlined at build/dev-server start, so restart the web server after changing it.

## 4. Run the checks

```bash
(cd apps/api && uv run ruff format --check . && uv run ruff check . && uv run mypy src)
(cd apps/api && uv run pytest -m "not live")        # 48 tests, no network
pnpm turbo lint build check-types                    # 12 tasks

# With both servers running:
node scripts/smoke-web.mjs                           # 6 routes, console errors
node scripts/a11y-check.mjs                          # axe, 0 violations
```

Live Qloo checks are opt-in and never run in CI: `(cd apps/api && uv run pytest -m live)`.

## 5. Key handling rules

- `.env` is gitignored; `apps/api/.env.example` contains empty values and is the only env file in git.
- Never log, trace, screenshot or paste keys. `/health` reports only `configured`/`unconfigured`.
- If a key leaks, rotate it in the provider dashboard before the demo.
- Removing `QLOO_API_KEY` is the kill switch: runs fail with `qloo_unconfigured` and produce zero partial ranking (tested).
- Removing `OLLAMA_API_KEY` degrades gracefully: manual item entry and `template` briefs, clearly labelled.

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Web shows network errors, API is up | Wrong API URL or CORS | Set `NEXT_PUBLIC_API_URL` to the API origin; add the web origin to `CORS_ORIGINS`; restart the web dev server |
| `localhost` fails but `127.0.0.1` works | IPv6 resolution mismatch | Use `127.0.0.1` in both URLs |
| Live run fails `qloo_unconfigured` | No key, or `.env` not loaded | Key in `apps/api/.env`; restart the API |
| Qloo 401 | Key/base URL/header | Check `QLOO_API_KEY` and `QLOO_BASE_URL=https://hackathon.api.qloo.com` |
| Qloo 429 or slow runs | Rate limit or budget | Keep `QLOO_RPS=4`; check the run counters and cache; cached calls are free |
| Ollama 401/404 or quota exhausted | Key or model name | Fix `OLLAMA_API_KEY` / `OLLAMA_MODEL`; without quota the app still completes with templates |
| Briefs say `template` | LLM unavailable or grounding rejected the output | Expected fallback; check `/health` and the run trace |
| `database is locked` | Concurrent SQLite writers | Already mitigated with WAL + 10 s busy timeout; run one API instance |
| `/sample` empty | Demo fixture missing or seed failed | Confirm `apps/api/data/demo/lisbon-run.json` exists and restart the API |
| `demo_read_only` 403 | Mutating the sample run | Expected; start your own run at `/start` |

## 7. Deploying (short version)

| Part | Where | Notes |
|---|---|---|
| API | Render / Railway / Fly.io, **one instance** | `uv run uvicorn tastebound_api.main:app --host 0.0.0.0 --port $PORT`; set every key as a server-side env var; rate limits and budgets are in-process |
| Web | Vercel, root `apps/web` | `NEXT_PUBLIC_API_URL` = public API URL; add the web origin to `CORS_ORIGINS` |
| DB | Supabase Cloud (optional) | Set `DATABASE_URL`; tables and the catalogue are created at startup; then seed the demo and set `DEMO_RUN_ID` if needed |

After deploying, open `/sample` in a private window (must work logged out), start one live run, and confirm `/health` before recording the demo.
