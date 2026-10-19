# 12. Acceptance criteria

Priority **MVP** must pass before submission; **Stretch** only if time allows. Record each result in `docs/progress.md` with the date and the test or evidence.

## Intake (F01)

| ID | Criterion | Check | Priority |
|---|---|---|---|
| INT-01 | With a website, at most 3 same-domain pages and 12,000 characters are read | Unit + API test | MVP |
| INT-02 | Proposed items validate (≤ 15, allowed kinds) or the user gets an empty editable list | Unit tests (FakeProvider) | MVP |
| INT-03 | Unreadable or missing website continues from the name with items labelled "general knowledge" | API test | MVP |
| INT-04 | Users can add, edit and remove items; confirmed items persist | API test | MVP |
| INT-05 | Website text is deleted after 30 days | Cleanup test | Stretch |

## Profile (F02)

| ID | Criterion | Check | Priority |
|---|---|---|---|
| PRF-01 | Every item ends resolved (with Qloo entity) or unresolved (with reason) | API test | MVP |
| PRF-02 | Entity ids come only from Qloo responses; LLM output is names only | Unit test | MVP |
| PRF-03 | Places must fall within the destination radius to be accepted | Unit test | MVP |
| PRF-04 | Profile tags follow the documented aggregation rule | Unit test | MVP |
| PRF-05 | Fewer than 3 resolved entities blocks the run with `profile_too_thin` | API test | MVP |

## Market scoring (F03)

| ID | Criterion | Check | Priority |
|---|---|---|---|
| MKT-01 | Each market has a target and a baseline query (or heatmap pair) in the trace, live or cached | Trace test | MVP |
| MKT-02 | Lift, taste score and confidence follow `04-qloo-integration.md`; a crafted fixture shows lift reordering raw scores | Unit tests | MVP |
| MKT-03 | Guards drop wrong-type or out-of-radius results and warn | Contract test | MVP |
| MKT-04 | One failing market is excluded with a warning; others are scored | Integration test | MVP |
| MKT-05 | Coverage and `thin_data` flags shown; confidence explained in the UI | Unit + UI check | MVP |
| MKT-06 | Rescore with new thresholds uses stored responses and makes zero Qloo calls | Integration test | MVP |

## Arrivals and gap (F04)

| ID | Criterion | Check | Priority |
|---|---|---|---|
| GAP-01 | CSV parsing handles BOM, quoted commas, bad numbers with row-level errors | Unit tests | MVP |
| GAP-02 | Origins match markets by city+country or by country (approximation labelled) | Unit tests | MVP |
| GAP-03 | Gap and quadrant computed exactly as documented, thresholds stored with the run | Unit tests | MVP |
| GAP-04 | Fewer than 5 matched markets disables the gap view with a notice | API test | MVP |
| GAP-05 | Arrivals source note is stored and shown wherever arrivals appear | API + UI check | MVP |

## Audience, angles, partners (F05–F07)

| ID | Criterion | Check | Priority |
|---|---|---|---|
| AUD-01 | Each shortlisted market has age and gender data from Qloo or an explicit "no data" state | API test | MVP |
| AUD-02 | Over-index is computed against a location-only baseline when available, otherwise labelled | Unit test | MVP |
| AUD-03 | No audience figure is ever produced by the LLM | Code review + test | MVP |
| ANG-01 | Each angle has ≥ 1 entity and ≥ 1 tag of evidence with source ids | API test | MVP |
| ANG-02 | Angle headline is a template over evidence values only | Unit test | MVP |
| ANG-03 | Explainability text is attached when available | Contract test | MVP |
| ANG-04 | Markets without per-entity data show "insufficient data" | API test | MVP |
| PAR-01 | Podcasts, artists, films and books per market come from location-aware Qloo calls | Trace test | MVP |
| PAR-02 | Partners ranked by lift over a baseline; a fixture shows the order differs from raw | Unit test | MVP |
| PAR-03 | Brands are queried globally, never with location, and labelled global | Unit test | MVP |
| PAR-04 | An empty type shows an empty state without affecting other types | UI check | MVP |

## Competitor positioning (F08)

| ID | Criterion | Check | Priority |
|---|---|---|---|
| CMP-01 | Compare call returns distinguishing tags and entities with evidence | Contract test | Stretch |
| CMP-02 | Panel hidden unless the feature is enabled | API test | Stretch |

## Budget, briefs, export (F09–F10)

| ID | Criterion | Check | Priority |
|---|---|---|---|
| BUD-01 | Shares sum exactly to the total and respect the minimum share | Unit test | MVP |
| BUD-02 | Locks and re-normalisation behave as documented in both modes | Unit tests | MVP |
| BUD-03 | Client and server compute identical allocations | Test with shared fixtures | MVP |
| BRF-01 | Grounding validator rejects invented numbers, names, unknown evidence ids and missing caveat | Unit tests | MVP |
| BRF-02 | After one failed repair, a template brief labelled `template` is used | Unit test | MVP |
| BRF-03 | Brief edits persist | API test | MVP |
| BRF-04 | CSV export has the documented columns, UTF-8 | Unit test | MVP |
| BRF-05 | Markdown export includes an evidence appendix with sources | Unit test | Stretch |

## Agent (F11)

| ID | Criterion | Check | Priority |
|---|---|---|---|
| AGT-01 | Plan guard refuses unknown tools, wrong order, foreign ids, repeated identical calls | Unit tests | MVP |
| AGT-02 | Each phase ends within `LLM_MAX_STEPS_PER_PHASE` | Unit test | MVP |
| AGT-03 | Two invalid steps or provider failure switch to the deterministic plan; reason recorded | Integration test | MVP |
| AGT-04 | SSE streams all event types and replays from `Last-Event-ID` | API test | MVP |
| AGT-05 | Trace lists LLM steps, tool calls and Qloo calls in order with no secrets | API test + string search | MVP |
| AGT-06 | Agent, planner and deterministic paths give identical scores for the same inputs and cache | Integration test | MVP |

## Demo and budget (F12)

| ID | Criterion | Check | Priority |
|---|---|---|---|
| DMO-01 | `/sample` works with Qloo and LLM keys unset | API test + manual | MVP |
| DMO-02 | Live runs limited per IP hash and workspace per day | API test | MVP |
| DMO-03 | An identical run within the TTL makes zero live Qloo calls | Integration test | MVP |
| DMO-04 | Hitting a cap keeps partial results and warns | Integration test | MVP |
| DMO-05 | At 80% of the monthly Qloo limit, new live runs are refused with a pointer to the sample | Unit test | MVP |

## Qloo (cross-cutting): "impossible without Qloo"

| ID | Criterion | Check | Priority |
|---|---|---|---|
| QLO-01 | Every score, gap, audience figure, angle evidence item and partner traces to stored Qloo responses (gap also to arrivals rows) | Integration test over a fixture run | MVP |
| QLO-02 | **Kill switch:** empty or invalid Qloo key → run fails at `build_profile` with `qloo_unconfigured`/`qloo_auth`; no scores, gaps, audiences, angles, partners or briefs; no brief LLM call | API test + manual on video | MVP |
| QLO-03 | A full run uses at least 5 Qloo capabilities in a dependent chain: search, tags, location-aware scoring with baseline, demographics, cross-domain partners (explainability counts if available) | Trace inspection | MVP |
| QLO-04 | Silent-failure guards run on every response | Contract tests | MVP |
| QLO-05 | Client never exceeds `QLOO_RPS` | Unit test (fake clock) | MVP |
| QLO-06 | Responses cached by normalised key; reused within TTL | Integration test | MVP |
| QLO-07 | `docs/qloo-contract.md` lists verified endpoints and parameters with fixtures for each | Review | MVP |

## LLM (cross-cutting)

| ID | Criterion | Check | Priority |
|---|---|---|---|
| LLM-01 | Provider names appear only under `llm/` | Grep test in CI | MVP |
| LLM-02 | Switching `LLM_PROVIDER` changes only prose; all numbers identical | Integration test | MVP |
| LLM-03 | Ollama Cloud called at `OLLAMA_BASE_URL` with Bearer key; no local Ollama installed or required | Manual on a machine without Ollama | MVP |
| LLM-04 | Invalid JSON → exactly one repair → documented fallback | Unit tests | MVP |
| LLM-05 | LLM calls per run ≤ `LLM_MAX_CALLS_PER_RUN` | Integration test | MVP |
| LLM-06 | `docs/llm-contract.md` records a real tool-calling exchange with the chosen model | Review | MVP |
| LLM-07 | Gemini (or another direct provider) works by env change only | Manual with a key, or mocked HTTP test | Stretch |

## Data, API, security, reliability

| ID | Criterion | Check | Priority |
|---|---|---|---|
| DAT-01 | Migrations apply to an empty database | `supabase db reset` | MVP |
| DAT-02 | RLS enabled on all tables, zero policies | SQL check | MVP |
| DAT-03 | Another workspace's run returns 404 | API test | MVP |
| API-01 | `openapi.json` and `packages/contracts` up to date | CI diff check | MVP |
| API-02 | Invalid input → 422 problem object | API tests | MVP |
| SEC-01 | No secrets in repo, logs, traces, responses or bundle | Secret scan + bundle search | MVP |
| SEC-02 | SSRF guard blocks private and metadata addresses including via redirects | Unit tests | MVP |
| SEC-03 | Rate limits on runs, intake, search | API tests | MVP |
| SEC-04 | Tampered or missing workspace token → 401 | API test | MVP |
| REL-01 | Retries with backoff on 429/5xx/timeouts | Integration tests | MVP |
| REL-02 | Every external call has a timeout | Code review + test | MVP |

## Frontend

| ID | Criterion | Check | Priority |
|---|---|---|---|
| UI-01 | Screens follow `docs/DESIGN.md` | Visual review | MVP |
| UI-02 | Gap quadrant and market table implemented with accessible equivalents | Manual + axe check | MVP |
| UI-03 | All states in `08-frontend-spec.md` reachable | Manual with forced failures | MVP |
| UI-04 | Tooltips on numbers; source chips link to trace | Manual | MVP |
| UI-05 | Keyboard-only Flow A; Lighthouse accessibility ≥ 90; 360 px | Lighthouse + manual | MVP |
| UI-06 | Copy never says "demand" or "will visit"; caveat visible | Text search | MVP |

## Evaluation and submission

| ID | Criterion | Check | Priority |
|---|---|---|---|
| EVL-01 | Evaluation metrics in `15-evaluation-and-backtest.md` computed and reported honestly | Review of `docs/evaluation-results.md` | MVP |
| EVL-02 | Backtest run if a multi-year arrivals series exists | Review | Stretch |
| REP-01 | Public repo with open-source `LICENSE` | Review | MVP |
| REP-02 | README: setup, architecture, Qloo chain, kill switch, evaluation, limits | Review | MVP |
| REP-03 | Clean clone runs with documented commands | Fresh environment | MVP |
| REP-04 | Demo URL works logged out, including `/sample` | Private window | MVP |
| REP-05 | Video public and matches the working app | Review | MVP |
| REP-06 | `docs/judge.md` run on the final build; report saved; top fixes applied or noted | `JUDGING_REPORT.md` | MVP |
