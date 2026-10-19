# TasteBound: documentation pack

**TasteBound** (working name; rename freely) is an agent for **tourism boards, regional tourism offices and hotel groups**. It answers: *"Which origin cities already love what our destination offers, which of them are not visiting yet, and how should we pitch each one?"*

It builds a **taste profile** of a destination from Qloo entities (its signature places, food, culture), scores **origin markets** by how strongly their residents over-index on that profile compared with a popularity baseline, compares that with **actual visitor arrivals** to find **untapped markets (gaps)**, and produces per-market **audience, campaign angle, media partners and budget split**, all traced to Qloo calls. An LLM writes the market briefs from that data only.

Built for the **Qloo Agentic Hackathon 2026** (deadline **Oct 30, 2026, 11:45pm EDT** = **Oct 31, 9:15am IST**).

Stack: Turborepo monorepo · **Next.js** (`apps/web`) · **FastAPI** (`apps/api`) · **Supabase** Postgres · **Ollama Cloud** (API key, never local; default model Gemma 4 31B) behind a provider layer portable to **Gemini** or any direct API (no OpenRouter) · **Qloo Taste AI**.

## Read in this order

| # | File | Covers |
|---|---|---|
| 1 | `docs/00-product-brief.md` | Problem, users, value, why Qloo, metrics |
| 2 | `docs/01-scope.md` | MVP, stretch, out of scope |
| 3 | `docs/02-user-flows.md` | Flows with diagrams |
| 4 | `docs/03-architecture.md` | Monorepo, components, data flow, config |
| 5 | `docs/features/F01`–`F12` | One file per feature: how it works, failures, UI, tests |
| 6 | `docs/04-qloo-integration.md` | **How Qloo is used**, multi-call chain, strategies, baseline, budget, kill switch |
| 7 | `docs/05-agent-and-llm.md` | Agent tools, Ollama Cloud, provider portability, prompts |
| 8 | `docs/06-data-model-supabase.md` | Tables and SQL |
| 9 | `docs/07-api-spec.md` | FastAPI endpoints |
| 10 | `docs/08-frontend-spec.md` | Screens and states (visuals from `DESIGN.md`) |
| 11 | `docs/09-data-sources.md` | Arrivals data, market catalogue, licences |
| 12 | `docs/10-security-and-privacy.md` | Secrets, data handling |
| 13 | `docs/11-plan.md` | Phases and day-by-day schedule |
| 14 | `docs/12-acceptance-criteria.md` | Numbered, testable criteria |
| 15 | `docs/13-test-plan.md` | What, how, commands |
| 16 | `docs/14-checks.md` | Per-commit, per-phase, pre-demo, pre-submit |
| 17 | `docs/15-evaluation-and-backtest.md` | Proving Qloo adds signal |
| 18 | `docs/16-runbook.md` | Setup, run, seed, deploy, troubleshoot |
| 19 | `docs/17-judging.md` | Rules, criteria mapping, self-score, demo script, Devpost text |
| 20 | `docs/18-risks-and-decisions.md` | Risks, Day 0 spikes, decisions |
| 21 | `docs/judge.md` | Protocol for an AI judge (with sub-agents) to score the built project |
| 22 | `docs/DESIGN.md` | **Placeholder: replace with your design file** |
| — | `AGENTS.md`, `CLAUDE.md`, `START_PROMPT.md` | Agent rules and the detailed first prompt |

## How to use

1. Copy this folder's contents into your Turborepo root so `docs/` sits beside `apps/` and `packages/`. Append this `AGENTS.md` to your existing one.
2. Replace `docs/DESIGN.md` with your design file.
3. Create `apps/api/.env` from `docs/03-architecture.md`.
4. Paste the prompt in `START_PROMPT.md` into your coding agent.

## Three rules above everything

1. **Qloo decides; the LLM narrates.** Market scores, gaps, audiences, angles' evidence and partners come from Qloo through deterministic code. The LLM picks tools and writes prose. It never invents a market, number or partner.
2. **Verify before building.** Every Qloo parameter and response field here is unverified until Phase 0 records it from a live call. Same for Gemma 4 tool calling on Ollama Cloud.
3. **Fail closed.** Without Qloo the app refuses to score markets. This "kill switch" is a tested feature that proves the app is impossible without Qloo.
