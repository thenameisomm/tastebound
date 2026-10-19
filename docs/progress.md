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
| PH8 | Tests: 48 passing (`uv run pytest -m "not live"`); unit (scoring, grounding, plan guard, arrivals, LLM parsing, Qloo client, website incl. redirect-to-private) + API (token, destinations, arrivals incl. bundled sample, kill switch, demo trace, 40-market cap, demo read-only); mypy strict + ruff clean | `apps/api/tests/` |
| PH8 | `packages/contracts` generated from OpenAPI (`src/api.ts`); contracts + web lint/check-types pass | `apps/api/scripts/export_openapi.py`, `pnpm --filter @repo/contracts generate` |
| PH9 | Frontend complete: landing, 4-step wizard, results (SSE live progress, gap quadrant, sortable/filterable market table, shortlist + deep dive), market detail (audience, angle + evidence, partners, brands), plan (budget split with locks, editable briefs, exports), trace, sample; design tokens per `docs/DESIGN.md` | `apps/web/`; smoke + axe scripts in `scripts/` |
| PH9 | Accessibility: 0 axe violations on all six routes; contrast fixes, SVG anchor points with text alternatives; 360 px layout (table → cards, quadrant scrolls) | `scripts/a11y-check.mjs` |
| PH9 | Fixed found bugs: SSE resume URL, terminal-run reconnect banner, quadrant percentile scale, SQLite `database is locked` under concurrent fetches (WAL + busy timeout), redirect content-type check, grounding name fragments | commits `80b6705`, `63277c8` |
| SUB | Judge protocol (`docs/judge.md`) run with independent J5/J6 audits; fixed sample-trace Qloo rows, 40-market cap, README/docs overclaims, `tools_ok` semantics, SSRF redirect test | `JUDGING_REPORT.md`; tests 48 |
| SUB | Second live destination (Kyoto, APAC-15): top five (Mumbai, Delhi, Kuala Lumpur, Sydney, Auckland) differs from Lisbon's (Cartagena, Tokyo, Kuala Lumpur, San Diego, Seattle) | run `f29c1697…`, 80 live Qloo calls |
| SUB | README product page, hero, six screenshots, MIT licence; axe 0 violations and Lighthouse accessibility 100 | `assets/readme/`, `scripts/readme-shots.mjs` |
| SUB | Visual redesign to `docs/DESIGN.md`: Inter (NotionInter substitute) + Source Serif (Lyon substitute), full token set, 64px nav with primary action, centered hero with avatar marks/highlight pill/product mockup with mockup shadow, accent feature blocks, greyscale chain wall, eyebrow cadence on all screen headers; axe 0 violations re-verified, smoke 6/6 | commits `bb8b338`…`0820f21`; screenshots refreshed `f04769c` |

## Acceptance status (live-verified, not yet test-coded)

- Intake with manual fallback; workspace sessions; presets; arrivals upload; run lifecycle to `done`; SSE events; deep dive; briefs list/patch/export; CSV export; trace — all exercised via curl on port 8020.
- Qloo calls spent: 152 live + 100 cached in the demo run; ~90 during spikes; 80 live for the Kyoto verification. Budget well under the monthly cap.
- UI-01..UI-06: screens follow `docs/DESIGN.md`; gap quadrant and table with accessible equivalents; states implemented (loading, live, partial, failure, no arrivals, thin data, empty filters, reconnect, 404); tooltips and source chips; copy rules respected. Lighthouse accessibility 100; smoke 6/6 with 0 console errors.

## Blockers

- **Ollama Cloud key quota exhausted** → agent tool calling and LLM-written briefs untested; briefs fall back to `source: "template"`. Need a working key or upgraded plan.
- Docker/Supabase unavailable locally → SQLite for now.

## Next

1. User-side submission items: push the repo to a public remote, deploy the demo URL (external hosting required), file the Devpost entry; video is not required by the rules.
2. Re-run `docs/14-checks.md`, then smoke + axe against the deployed URL.
3. If an Ollama Cloud key with quota is available: verify tool calling, then (only then) enable `LLM_TOOL_CALLING` and claim it.
