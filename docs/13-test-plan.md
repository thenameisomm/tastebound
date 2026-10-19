# 13. Test plan

## Layers

| Layer | Tools | Network | CI | Proves |
|---|---|---|---|---|
| Unit | pytest | none | yes | Scoring maths, gap, allocation, guards, matching, validators, CSV parsing |
| Contract | pytest + recorded fixtures | none | yes | Qloo and Ollama responses parse with our models; guards |
| Integration | pytest + respx + test DB | none | yes | Qloo client (rate, retries, cache, budget, trace), tools, agent with FakeProvider, repositories |
| API | httpx/TestClient + FakeProvider + fixtures + test DB | none | yes | Endpoints, validation, SSE, scoping, kill switch, demo |
| Web unit | Vitest + Testing Library | none | yes | Components (quadrant, table, sliders), hooks, SSE reducer |
| End-to-end | Playwright vs API in `APP_ENV=test` | none to third parties | yes | Flow A to export; Flow B sample; error states |
| Live smoke | pytest `-m live` | real | **no** | One real run for the demo destination |
| Evaluation | `scripts/evaluate.py`, `scripts/backtest.py` | real (cached) | no | Qloo adds signal (see `15-evaluation-and-backtest.md`) |

**Fixture mode:** `APP_ENV=test` swaps external clients for fixture-backed fakes reading `apps/api/tests/fixtures/<service>/`. A missing fixture fails loudly. Fixtures are recorded with `scripts/record_fixture.py`, keys stripped.

**Test database:** local `supabase start` + `supabase db reset`, or a dedicated cloud test project in `TEST_DATABASE_URL`. Never production.

## Commands

```bash
# apps/api
uv run ruff check . && uv run ruff format --check .
uv run mypy src
uv run pytest -m "not live" --cov=tastebound_api --cov-report=term-missing
uv run pytest -m live -k smoke          # manual; spends real calls

# web and repo
pnpm --filter web lint && pnpm --filter web typecheck && pnpm --filter web test
pnpm --filter web exec playwright test
pnpm turbo lint test build
```

Coverage targets: 85% for `scoring/`, `qloo/`, `agent/`, `arrivals/`, `grounding.py`; 70% overall API.

## Matrix (feature → tests → IDs)

| Feature | Key tests | IDs |
|---|---|---|
| F01 | SSRF cases; page selection; text cap; parse/repair/fallback | INT-01..05, SEC-02 |
| F02 | Name matching; radius; tag rule; minimum entities; type guard | PRF-01..05 |
| F03 | Percentile/lift/score; lift reorders fixture; confidence; guards; single-market failure; rescore no calls | MKT-01..06, QLO-01..05 |
| F04 | CSV edge cases; matching; gap/quadrant; <5 matches; source note | GAP-01..05 |
| F05 | Over-index maths; missing baseline label; no LLM numbers | AUD-01..03 |
| F06 | Evidence selection; template-only headline; explainability optional | ANG-01..04 |
| F07 | Lift vs raw; brands global; empty tab | PAR-01..04 |
| F09 | Sums; minimum share; locks; modes; client = server | BUD-01..03 |
| F10 | Validator cases; template fallback; edits; CSV; Markdown | BRF-01..05 |
| F11 | Guard; step limit; fallback; identical scores across paths; SSE replay; trace no secrets | AGT-01..06 |
| F12 | Sample without keys; limits; zero live calls cached; monthly guard; caps | DMO-01..05 |
| Data/API/Security | Migrations; RLS query; scoping; OpenAPI diff; 422s; token tamper; rate limits | DAT, API, SEC, REL |
| UI | Component tests; Playwright flows; forced errors; Lighthouse; axe | UI-01..06 |

## Named failure scenarios (each has a test)

1. No Qloo key → kill switch. 2. Qloo 401 mid-run. 3. Qloo 429 storm → `qloo_rate_limited`. 4. 200 response with wrong entity type → contract violation. 5. Market results outside radius → dropped with warning. 6. Only US markets have data → coverage warning and low confidence elsewhere. 7. Ollama 401 → deterministic plan, template briefs. 8. Gemma returns text instead of tool calls twice → fallback. 9. Website redirect to `169.254.169.254` → blocked. 10. CSV with BOM and quoted commas. 11. Arrivals matched for 4 markets → gap view disabled. 12. Brief cites a number not in evidence → rejected. 13. Budget slider locks all but one market → remainder assigned correctly. 14. Other workspace's run → 404. 15. SSE drop mid-run → replay without duplicates.

## RLS check (DAT-02)

```sql
select c.relname, c.relrowsecurity from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r';     -- all true
select * from pg_policies where schemaname = 'public';  -- zero rows
```

## Manual script before recording

1. Private window → `/sample` → quadrant, market detail, plan, trace.
2. Live run for the demo destination with the sample arrivals → table in ≤ 90 s warm.
3. Shortlist 4 markets → deep dive → budget slider → edit a brief → export CSV.
4. Invalid Qloo key → kill switch error → restore.
5. `LLM_PROVIDER=fake` → identical numbers, different prose.
6. Keyboard-only pass; 360 px check.
