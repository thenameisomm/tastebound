# Progress

Updated 2026-10-19. Phases per `docs/11-plan.md`.

## Completed

| Phase | What | Evidence |
|---|---|---|
| PH0 | Qloo contract verified live; strategy P chosen; raw-lift correction | `docs/qloo-contract.md`; Lisbon spike over 68 markets, population corr 0.026 |
| PH0 | LLM transport verified until quota exhausted; tool calling recorded as unverified | `docs/llm-contract.md` |
| PH1 | FastAPI app: settings, errors, SQLite/Supabase-portable db layer, 68-market catalogue, arrival samples | `apps/api/src/tastebound_api/db/`, `data/markets.json` |
| PH2 | Qloo client: token bucket 4 rps, retries, cache, per-run/monthly budgets, trace rows, typed errors | `qloo/client.py`, `qloo/service.py` |
| PH3 | Scoring: raw-lift taste scores, gap vs arrivals, quadrants, allocator | `scoring/markets.py`, `scoring/gap.py`, `scoring/allocation.py` |
| PH4 | Arrivals parser + matcher (25 sample rows → 46 markets, 24 countries) | `arrivals/` |
| PH5 | Executor: full run, deep dive, counters, events, status/error handling, template briefs + grounding validator | `agent/executor.py`, `grounding.py` |
| PH6 | HTTP API: sessions, markets, intake, arrivals upload, runs (SSE), profile, markets, detail, allocation, rescore, briefs, exports, trace, demo | `routes/`, `main.py` |
| PH7 | Live E2E: Lisbon run `e5b2b8fd-…` done; 6 briefs; 68 scored markets; Cartagena rank 1 (99.26, gap 0.98); allocation 250k EUR works | `/tmp/tb-flow.json` |
| PH7 | Demo fixture exported and seeded: `data/demo/lisbon-run.json` (68 markets, 48 audience rows, 6 angles, 250 partners, 6 briefs) | `GET /v1/demo` 200; demo run read-only for other workspaces (403 `demo_read_only`) |
| PH8 | Tests: 46 passing (`uv run pytest -m "not live"`); unit (scoring, grounding, plan guard, arrivals, LLM parsing, Qloo client, website) + API (token, destinations, arrivals incl. bundled sample, kill switch, demo read-only); mypy strict + ruff clean | `apps/api/tests/` |
| PH8 | `packages/contracts` generated from OpenAPI (`src/api.ts`); contracts + web lint/check-types pass | `apps/api/scripts/export_openapi.py`, `pnpm --filter @repo/contracts generate` |
| PH9 | Frontend complete: landing, 4-step wizard, results (SSE live progress, gap quadrant, sortable/filterable market table, shortlist + deep dive), market detail (audience, angle + evidence, partners, brands), plan (budget split with locks, editable briefs, exports), trace, sample; design tokens per `docs/DESIGN.md` | `apps/web/`; smoke + axe scripts in `scripts/` |
| PH9 | Accessibility: 0 axe violations on all six routes; contrast fixes, SVG anchor points with text alternatives; 360 px layout (table → cards, quadrant scrolls) | `scripts/a11y-check.mjs` |
| PH9 | Fixed found bugs: SSE resume URL, terminal-run reconnect banner, quadrant percentile scale, SQLite `database is locked` under concurrent fetches (WAL + busy timeout), redirect content-type check, grounding name fragments | commits `80b6705`, `63277c8` |

## Acceptance status (live-verified, not yet test-coded)

- Intake with manual fallback; workspace sessions; presets; arrivals upload; run lifecycle to `done`; SSE events; deep dive; briefs list/patch/export; CSV export; trace — all exercised via curl on port 8020.
- Qloo calls spent: 152 live + 100 cached in the demo run; ~90 during spikes. Budget well under the monthly cap.
- UI-01..UI-06: screens follow `docs/DESIGN.md`; gap quadrant and table with accessible equivalents; states implemented (loading, live, partial, failure, no arrivals, thin data, empty filters, reconnect, 404); tooltips and source chips; copy rules respected. Lighthouse run still pending.

## Blockers

- **Ollama Cloud key quota exhausted** → agent tool calling and LLM-written briefs untested; briefs fall back to `source: "template"`. Need a working key or upgraded plan.
- Docker/Supabase unavailable locally → SQLite for now.

## Next

1. README + screenshots (Playwright); Lighthouse pass; `docs/judge.md` before submission.
2. Update `docs/14-checks.md` run before final commit.
