# 13. Test plan

## What is tested

| Layer          | Tools                                            | Network            | Purpose                                                                                                                                            |
| -------------- | ------------------------------------------------ | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Unit           | pytest                                           | none               | Scoring, percentiles, gap, allocation, arrivals matching, grounding, plan-guard helpers, LLM JSON parsing, website SSRF checks, Qloo client guards |
| API            | pytest + httpx ASGI transport + temporary SQLite | none               | Workspace auth, destination/profile flow, arrivals upload and bundled sample, kill switch, market cap, read-only demo, structured warnings         |
| Web components | Vitest + Testing Library + jsdom                 | none               | Assistant drawer/provider behavior, errors, conversation restore and optimistic rollback                                                           |
| Browser checks | Playwright + axe scripts under `scripts/`        | local API/web only | Smoke routes, console errors, accessibility scan, README screenshots                                                                               |
| Live           | pytest `-m live`                                 | Qloo/LLM           | Opt-in verification only; never in CI                                                                                                              |

Tests never call Qloo, Ollama or any other third party. HTTP is mocked with `respx`; the model is replaced with `FakeProvider` when a test needs model output.

## Commands

```bash
# API
cd apps/api
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -m "not live" -q

# Web component tests (also run by root pnpm test)
pnpm --filter web test

# Web, contracts and repo
pnpm turbo lint check-types build
pnpm test                                  # API + web test tasks

# Browser checks (with both servers running)
node scripts/smoke-web.mjs
node scripts/a11y-check.mjs
```

The API suite uses the test settings in `apps/api/tests/conftest.py`: `APP_ENV=test`, a temporary SQLite database, a fixed session secret and empty Qloo/LLM keys. It does not read the developer's `.env` values.

## Coverage by feature

| Feature                             | Key tests                                                                                                                                                                                                                                                   |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F01 intake                          | Website page cap, robots, non-HTML, redirect/SSRF blocks, 12,000-character cap                                                                                                                                                                              |
| F02 profile                         | Item matching, place rejection, profile dedupe and persistence                                                                                                                                                                                              |
| F03 scoring                         | Percentile ties, lift reordering raw affinity, confidence/thin data, population correlation                                                                                                                                                                 |
| F04 gap                             | CSV headers/BOM/quoted commas, bad rows, accents, city/country matching, quadrant thresholds                                                                                                                                                                |
| F05–F07 audiences, angles, partners | Implemented through the deterministic executor and fixture-backed API paths; full per-market audience coverage is a known limitation                                                                                                                        |
| F09 allocation                      | Sum, minimum share, locks and renormalisation                                                                                                                                                                                                               |
| F10 briefs                          | Grounding rejection for numbers/names/evidence/caveat; template fallback; persistence                                                                                                                                                                       |
| F11 orchestration                   | Plan-guard ordering/duplicates/step limit unit tests; deterministic executor; SSE replay and trace checks in API/browser tests                                                                                                                              |
| F12 demo                            | Keyless `/sample`, read-only demo, 40-market cap                                                                                                                                                                                                            |
| F13 results assistant               | No-provider 503; grounded answer/evidence; one repair; ungrounded leaves no partial history; workspace scoping; rate limit; blank message; web tests for open/answer/evidence/follow-up, unavailable state, sessionStorage restore and failed-send rollback |
| Qloo client                         | Fail-closed unconfigured client, cache reuse, RPS spacing, auth not retried, per-run budget, call tracing                                                                                                                                                   |
| Security                            | Workspace token required, demo write rejection, SSRF private-host blocks                                                                                                                                                                                    |

## Named failure scenarios

1. No Qloo key → kill switch (`qloo_unconfigured`).
2. Qloo 401 → `qloo_auth`, no retry.
3. Cache hit → no second HTTP request.
4. More than 40 markets → request rejected.
5. Website redirect to a private address → blocked.
6. CSV with BOM, quoted commas and bad rows → row-level errors.
7. Fewer than five arrivals matches → gap view disabled.
8. Brief citing an invented number or unknown evidence ID → grounding rejection.
9. Other workspace's demo write → `demo_read_only`.
10. Missing or tampered workspace token → 401.
11. Assistant with no provider → `enabled=false` and `assistant_unavailable`; run pages remain usable.
12. Assistant answer with an invented number or unknown evidence ID → repair → `assistant_ungrounded`, no partial assistant message.
13. Assistant from another workspace → 404; message limit → 429 before the provider call.

## Manual verification before a demo

1. Private window → `/sample` → quadrant, market detail, plan, trace.
2. Live run for the demo destination with the sample arrivals → results render and the trace updates.
3. Shortlist 4 markets → deep dive → budget slider → edit a brief → export CSV.
4. Invalid Qloo key → kill switch error → restore the key.
5. Keyboard-only pass through intake, results, market detail and plan.
6. 360 px viewport check for the assistant drawer, tables and charts; keyboard open, send, evidence-link and close path.

## Limits

- The suite does not exercise real Qloo coverage, real model output or a real LLM tool-choice loop. Those are covered only by opt-in live checks or are knowingly out of scope. Assistant tests use a fake provider and temporary in-memory stores.
- The browser scripts are checks, not a full Playwright test suite. The web tests cover assistant state transitions, not every page.
- Multi-instance assistant rate limiting and conversation sharing are not tested because the current store/limiter are process-local.
- Coverage percentages are not currently enforced in CI.
