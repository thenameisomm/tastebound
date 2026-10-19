# Start prompt for the coding agent

Paste everything in the block below into your coding agent (Claude Code or similar) from the repo root.

```text
ROLE
You are the lead engineer building "TasteBound" in this existing Turborepo. Work carefully, verify before you build, and keep the docs true.

REPO TODAY
- pnpm Turborepo. apps/web = Next.js App Router (default starter: app/layout.tsx, app/page.tsx, Geist fonts). apps/api = empty folder. packages/ui (button, card, code), packages/eslint-config, packages/typescript-config. Root AGENTS.md, turbo.json, pnpm-workspace.yaml.
- The docs pack has been copied in: README.md, AGENTS.md (append its content to the existing AGENTS.md if you find two), CLAUDE.md, START_PROMPT.md, docs/00–18, docs/features/F01–F12, docs/judge.md, docs/DESIGN.md.

WHAT WE ARE BUILDING
TasteBound helps tourism boards (DMOs), regional tourism offices and hotel groups decide which origin cities to target. For a destination it:
1) builds a Qloo taste profile from 5–15 signature items (places, food, culture, music, film, books),
2) scores 20–40 origin markets by taste lift over a popularity baseline (Qloo, location-aware),
3) compares taste with real visitor arrivals to find UNTAPPED markets (gap quadrant),
4) for 3–6 shortlisted markets: Qloo audience (age, gender), campaign angle with Qloo evidence, media partners (podcasts, artists, films, books) via cross-domain Qloo calls,
5) splits a budget across markets and writes grounded one-page market briefs; exports CSV and Markdown.
It is for the Qloo Agentic Hackathon 2026 (deadline Oct 30, 2026, 11:45pm EDT). Judges score: how thoroughly and skillfully we use Qloo (tie-breaker), complete product design, credible impact for a real audience, and a non-obvious idea. Qloo says: "If your submission would work the same without Qloo, you're building the wrong thing."

STACK (fixed)
- apps/api: Python 3.12, uv, FastAPI, httpx, Pydantic v2, pydantic-settings, asyncpg, trafilatura, pytest, respx, ruff, mypy. apps/api/package.json with wrapper scripts (dev, lint, test, build) so turbo runs it.
- apps/web: the existing Next.js app; types from packages/contracts (generated with openapi-typescript from apps/api/openapi.json).
- Database: Supabase Postgres via asyncpg; SQL migrations in supabase/migrations; RLS on every table with no policies; browser never talks to Supabase.
- LLM: Ollama Cloud over HTTPS with an API key (POST https://ollama.com/api/chat, Authorization: Bearer OLLAMA_API_KEY). NEVER run or require a local Ollama. Default model Gemma 4 31B; confirm the exact API model name from https://ollama.com/api/tags. Provider layer (llm/base.py) with OllamaCloudProvider, GeminiProvider, OpenAICompatProvider, FakeProvider; switch by LLM_PROVIDER env only. No OpenRouter or other gateways. Ollama Cloud does not support structured outputs: use prompt-and-validate JSON with one repair retry.
- Qloo: hackathon API (base URL and header in docs/04-qloo-integration.md), 5 req/s, 10,000 calls/month.

READ FIRST, IN ORDER
README.md → AGENTS.md → CLAUDE.md → docs/00 to docs/18 → docs/features/F01 to F12 → docs/judge.md → docs/DESIGN.md. If docs/DESIGN.md starts with PLACEHOLDER, do NOT build UI screens until I replace it; you may build the API client, generated types, hooks and state logic.

NON-NEGOTIABLE RULES
1. Qloo decides, the LLM narrates. Scores, gaps, audiences, angle evidence and partners come from Qloo through pure functions in scoring/. The LLM only proposes signature item NAMES, chooses tools, and writes briefs that must pass grounding.py. Angle headlines are templates.
2. Verify before coding. Every Qloo parameter and response field in the docs is UNVERIFIED. Call each endpoint live once, save the raw response as a fixture (keys stripped) under apps/api/tests/fixtures/qloo/, write docs/qloo-contract.md, and build Pydantic models from fixtures. Never guess parameter names.
3. Fail closed. Without a working Qloo key the run must fail at build_profile with qloo_unconfigured or qloo_auth and produce nothing else (kill switch, acceptance QLO-02).
4. Multi-call chain. A full run uses a dependent chain of Qloo calls: search → tags → per-market target + baseline (or the heatmap pair) → demographics, explanations/tags, cross-domain partners per shortlisted market (docs/04).
5. Agentic. Implement the tool-using agent in docs/05 and F11: native tool calls on Ollama Cloud, a plan guard (allowed tools, order, argument validation, no repeats), a planner variant (JSON actions) if native tool calls fail, and a deterministic fallback that runs the same tools. Agent, planner and deterministic paths must produce identical numbers (AGT-06).
6. Secrets stay server-side. Tests never touch the network (fixtures + respx). Live checks only via scripts in apps/api/scripts/ and you report how many Qloo calls you spent.
7. Honest copy: "taste fit", never "demand"; show arrivals sources; label templates and inferences.
8. No scope beyond docs/01-scope.md without asking.

PHASE 0 (do this first, then STOP)
Goal: prove the Qloo approach works before building the app.
1. Check the repo against docs/03-architecture.md (pnpm-workspace includes apps/* and packages/*). Report differences.
2. Scaffold apps/api: pyproject (uv), src/tastebound_api with settings.py (every env var in docs/03), errors.py, main.py with GET /health, package.json wrapper scripts, .env.example (no real values), .gitignore entries. Add ruff, mypy, pytest config.
3. Ask me for: QLOO_API_KEY, OLLAMA_API_KEY, DATABASE_URL (Supabase), two contrasting candidate destinations (suggest Lisbon, PT and Kyoto, JP), and whether I have an arrivals CSV. Continue with everything that doesn't need a missing item; list exactly what is blocked.
4. Write apps/api/src/tastebound_api/data/markets.json: 60–80 origin cities (id like "gb-london", city, ISO country, region, lat, lon, radius_km 40, population_band 1–5) with preset groups europe20, na15, apac15, me8, latam10. Note the reference you used in a header field.
5. Write scripts/spike_qloo.py and run spikes S1–S5 from docs/18 for both destinations over at least 20 markets in 3+ regions:
   - resolve 12 signature items each; check whether each destination is itself a Qloo destination/locality entity;
   - run scoring strategies D, P and H (docs/04) with baselines; record per-market result counts (coverage), rankings, Spearman with population band, top-10 Jaccard between the two destinations, and non-US coverage;
   - demographics with location (with and without the taste signal) for 3 markets;
   - podcasts, artists, films, books with location for 3 markets; overlap between markets; lift vs raw;
   - explainability availability and cost.
   Respect 4 req/s, cache responses, and keep total Phase 0 Qloo calls under 600.
6. Write scripts/spike_llm_tools.py: 5 two-tool round trips with Gemma 4 on Ollama Cloud (S6). Record a real exchange in docs/llm-contract.md, including the exact model name.
7. S7: look for an openly licensed arrivals-by-origin dataset for each candidate destination (≥ 15 origin markets overlapping the catalogue). Report source, licence and URL; do not scrape sites that forbid it.
8. Write docs/qloo-contract.md (verified endpoints, params, response shapes, quirks), save fixtures, create docs/progress.md with all numbers, recommend the scoring strategy and the demo destination, and log decisions in docs/18-risks-and-decisions.md.
9. Report the go/no-go result (docs/11 and docs/18 thresholds) with numbers and Qloo calls spent. STOP and wait for my approval.

AFTER APPROVAL
Follow docs/11-plan.md phases 1→7 in order:
- Phase 1 foundations (settings, Supabase migration 0001 from docs/06, workspace token, Qloo client with rate limit/retries/cache/budget/trace/guards, market catalogue loader).
- Phase 2 scoring engine (F02, F03, F04 tools, deterministic plan, run lifecycle, SSE).
- Phase 3 agent + intake (F01, F11, provider layer, prompts).
- Phase 4 deep dive (F05, F06, F07, F09, F10).
- Phase 5 frontend once docs/DESIGN.md is real (all screens and states in docs/08; the gap quadrant and market table are the hero visuals).
- Phase 6 demo seed, evaluation and backtest (docs/15), deploy (docs/16).
- Phase 7 README, LICENSE, video support, Devpost text from docs/17, then run docs/judge.md and save JUDGING_REPORT.md.
After each phase: run docs/14-checks.md, record passing acceptance IDs (docs/12) in docs/progress.md with test names, commit with IDs in messages, and summarise in under 10 lines. Ask only when blocked. When live behaviour contradicts the docs, trust live behaviour, update the docs and log the decision.

DEFINITION OF DONE
All MVP acceptance criteria pass; kill switch works; agent/planner/deterministic paths give identical numbers; sample run works logged out without keys; evaluation reported honestly; deployed demo and public repo with LICENSE; JUDGING_REPORT.md produced.

Begin with Phase 0, step 1.
```

## Notes for you

- Have ready: Qloo hackathon key, Ollama Cloud key, Supabase connection string, and (if you have one) an arrivals CSV.
- Upload your design to `docs/DESIGN.md` before Phase 5.
- The Phase 0 go/no-go is the most important checkpoint. If Qloo can't separate origin markets beyond population, or coverage outside the US is thin, switch to the fallback project rather than pushing on.
