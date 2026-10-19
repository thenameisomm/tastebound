# TasteBound — Hackathon Checklist

> **Deadline**: Oct 30, 2026 11:45 PM EDT  
> **Repo**: https://github.com/thenameisomm/tastebound  
> **JUDGING_REPORT**: 16/20 (C1-C4 = 4 each), Stage 1: 6/8 PASS

---

## Phase 0 — Discovery & Contracts ✅ DONE

- [x] Qloo API contract recorded (`docs/qloo-contract.md`)
- [x] Fixtures captured from live calls (252 Qloo calls in Lisbon demo)
- [x] LLM contract recorded (`docs/llm-contract.md`) — Gemma 4 31B on Ollama Cloud, tool calling unverified
- [x] Design spec written (`docs/DESIGN.md`) — Notion-style tokens, components, layout

---

## Phase 1 — Backend Core ✅ DONE

- [x] FastAPI project structure (`apps/api/src/tastebound_api/`)
- [x] Database models (Destinations, SignatureItems, Runs, Markets, Arrivals, Briefs, Allocations, QlooCalls, Traces)
- [x] Migrations + SQLite dev / Postgres prod
- [x] Qloo client: search, tags, insights (target + baseline), demographics, partners
- [x] Scoring pipeline: lift = target − baseline; percentile per run; quadrants; confidence
- [x] Arrivals ingestion + gap analysis
- [x] Agent executor: phased run (profile → score → gap → deep-dive → budget → briefs)
- [x] Deterministic fallback when LLM unavailable (`LLM_TOOL_CALLING=false`)
- [x] Grounding layer: every brief claim traced to Qloo evidence
- [x] Trace logging: every Qloo call, tool step, warning recorded
- [x] API routes: destinations, markets, runs, plan, trace, arrivals, workspaces
- [x] Workspace token auth (`X-Workspace-Token`)
- [x] Kill switch: no ranking without Qloo (fail closed outside `APP_ENV=test`)
- [x] Rate limiting ≤ 4 req/s; cache per docs; monthly budget guard
- [x] Settings: `max_markets_per_run = 40`, `llm_tool_calling = false`

---

## Phase 2 — Frontend Core ✅ DONE

- [x] Next.js 14 app router (`apps/web/app/`)
- [x] 7 screens: Landing, Start wizard, Results, Market detail, Plan, Trace, Sample
- [x] Contracts package (`packages/contracts`) generated from OpenAPI
- [x] TanStack Query + React Hook Form + Zod
- [x] SSE live updates for run progress
- [x] Server-side API proxy (no browser calls to Qloo/Ollama/Supabase)
- [x] Axe 0 violations (initial), Lighthouse a11y 100

---

## Phase 3 — Demo & Fixtures ✅ DONE

- [x] Lisbon demo fixture (`apps/api/data/demo/lisbon-run.json`) — 252 Qloo calls
- [x] Demo seed reconstructs trace from fixture (delete-by-call-id for idempotency)
- [x] Sample run endpoint `/sample` — read-only, no Qloo quota
- [x] 48 tests passing (unit + API, no network, respx fixtures)
- [x] SSRF redirect test (`test_redirect_to_private_host_is_blocked`)
- [x] 40-market cap enforced at route + schema level

---

## Phase 4 — Judging Protocol ✅ DONE

- [x] J5 (novelty/impact) audit — nearest: GeoTaste, Transplant, Taste Transplant, Cross Cultura Pro
- [x] J6 (security/claims) audit — secrets clean, .env untracked, SSRF pass, copy honesty fixes
- [x] Lead judge (J1–J4, J7) — `JUDGING_REPORT.md` written
- [x] Scores: C1 4, C2 4, C3 4, C4 4 = **16/20**
- [x] Claims tested: 11 claims, claim 8 ("agent chooses tools") corrected to FALSE
- [x] Fixes shipped:
  - Trace seeding (252 QlooCall rows)
  - 40-market cap
  - Honest copy (lift formula, agent role, tools_ok semantics)
  - `LLM_TOOL_CALLING=false` setting
  - SSRF test
  - `.env` chmod 600
- [x] Kyoto live verification (run `f29c1697…`, 80 live calls, different rankings → claim 3 verified)

---

## Phase 5 — Documentation ✅ DONE

- [x] `docs/19-setup.md` — step-by-step key acquisition (Qloo via docs.qloo.com form → hackathon@qloo.com email; Ollama Cloud keys; minimal .env)
- [x] `docs/14-checks.md` — pre-demo / pre-submit checklists
- [x] `docs/17-judging.md` — Devpost skeleton, demo run-through (video NOT required per Oct 19 Devpost page)
- [x] `docs/18-risks-and-decisions.md` — 5 decision rows appended
- [x] `docs/progress.md` — all phases logged
- [x] `README.md` — product page, 6 screenshots, MIT license, setup link
- [x] `LICENSE` (MIT, Om Badgujar)
- [x] `JUDGING_REPORT.md` — full structure per `docs/judge.md`

---

## Phase 6 — Visual Redesign (docs/DESIGN.md) ✅ DONE

- [x] **Foundation** (`bb8b338`): Full Notion token set; Inter (NotionInter substitute) + Source Serif 4 (Lyon substitute) via `next/font/google`; 64px sticky nav with centered links + primary CTA; decorative marks (avatar row, squiggle, sparkle, flower)
- [x] **Landing** (`aad3b91`): Centered hero — avatar marks → 72px display with peach highlight pill → serif subhead → CTA row → product mockup with `--shadow-mockup`; step cards; marigold/midnight accent blocks; greyscale chain wall
- [x] **Screens** (`89c7279`): Eyebrow cadence on all headers; serif intro on wizard; stale lift tooltip corrected ("target vs baseline affinity")
- [x] **Contrast fix** (`0820f21`): `.eyebrow` 60% ink for AA
- [x] **Screenshots refreshed** (`f04769c`) — 6 new PNGs in `assets/readme/`
- [x] **Progress recorded** (`6514828`)

---

## Phase 7 — Public Repo & Kill-Switch ✅ DONE

- [x] Repo published: https://github.com/thenameisomm/tastebound
- [x] MIT license visible in About section
- [x] Clean history (no secrets, .env untracked, 475 KiB pack)
- [x] Kill-switch rehearsal verified: invalid QLOO_API_KEY → run fails with `qloo_auth`, zero counters, empty shortlist
- [x] Pre-demo checks all ticked in `docs/14-checks.md`
- [x] `JUDGING_REPORT.md` Stage 1 updated: items 1, 2(a), 4, 5, 6, 7 = PASS
- [x] Final turbo/lint/build/check-types: 12/12 ✅
- [x] Final tests: 48/48 ✅
- [x] Final smoke: 6/6 ✅
- [x] Final axe: 0 violations ✅

---

## Phase 8 — External Deployment 🔄 USER ACTION REQUIRED

> **Blocker for Stage 1 item 3** (hosted demo) and item 8 (description matches deployed)

### API Deployment
- [ ] Choose host: Fly.io / Render / Railway / VPS
- [ ] Provision PostgreSQL (or use managed)
- [ ] Set env vars:
  - `QLOO_API_KEY` (from Qloo hackathon email)
  - `OLLAMA_API_KEY` (from ollama.com/settings/keys)
  - `SESSION_SECRET` (`openssl rand -hex 32`)
  - `DATABASE_URL` (PostgreSQL connection string)
  - `WORKSPACE_SECRET` (for token signing)
  - `APP_ENV=production`
  - `LLM_TOOL_CALLING=false`
- [ ] Deploy API (Docker or uv + uvicorn)
- [ ] Verify `/health` → `qloo: "configured"`, `tools_ok: false`

### Web Deployment
- [ ] Deploy to Vercel (recommended) or any Node host
- [ ] Set env vars:
  - `NEXT_PUBLIC_API_URL` → deployed API URL
  - `WORKSPACE_SECRET` (same as API)
- [ ] Verify all 7 routes load, SSE works, sample run accessible

### Post-Deploy Verification
- [ ] Run smoke + axe against deployed URLs
- [ ] Update `JUDGING_REPORT.md` row 3 → PASS with deployed URL
- [ ] Re-verify row 7 (free unrestricted testing) and row 8 (description matches) on deployed demo
- [ ] Update `docs/14-checks.md` Pre-submit ticks
- [ ] Optional: Lighthouse CI on deployed URLs

---

## Phase 9 — Final Submission 🔄 USER ACTION REQUIRED

- [ ] Devpost project created
- [ ] Devpost fields filled from `docs/17-judging.md` skeleton
- [ ] Public repo URL added
- [ ] Deployed demo URL added
- [ ] Text description pasted
- [ ] License confirmed visible in GitHub About
- [ ] Submit ≥ 24 hours before deadline (by Oct 29 11:45 PM EDT)

---

## Summary

| Phase | Status | Notes |
|-------|--------|-------|
| 0 Discovery | ✅ | Contracts frozen |
| 1 Backend | ✅ | 48 tests, kill switch, rate limits |
| 2 Frontend | ✅ | 7 screens, SSR proxy |
| 3 Demo | ✅ | Lisbon fixture, Kyoto verified |
| 4 Judging | ✅ | 16/20, report written |
| 5 Docs | ✅ | Setup guide, checklists, progress |
| 6 Redesign | ✅ | Full DESIGN.md compliance |
| 7 Repo/Rehearsal | ✅ | Public, kill-switch verified |
| 8 Deploy | 🔄 | **Only remaining technical work** |
| 9 Submit | 🔄 | Devpost form fill |

---

**Next command to run after deployment**:
```bash
# Update judging report with deployed URLs, then:
git add JUDGING_REPORT.md docs/14-checks.md docs/progress.md
git commit -m "docs: deployed demo URL; Stage 1 complete [SUB]"
git push
```