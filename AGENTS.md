# AGENTS.md: TasteBound

(Append to the repo's existing AGENTS.md.)

## What this repo builds

TasteBound, for the Qloo Agentic Hackathon 2026: Next.js (`apps/web`) + FastAPI (`apps/api`) + Supabase Postgres. For a destination, it builds a Qloo taste profile, scores origin markets by taste lift over a popularity baseline, compares with real arrivals to find untapped markets, and produces per-market audiences, campaign angles, media partners, a budget split and grounded briefs. The agent runs on Ollama Cloud (Gemma 4 31B by default) behind a portable provider layer.

Read `README.md`, then `docs/` in numbered order and `docs/features/`, before writing code.

## Hard rules

1. **Qloo decides; the LLM narrates.** Scores, gaps, audiences, angle evidence and partners come from Qloo through pure functions in `scoring/`. The LLM proposes item names, chooses tools, and writes briefs that pass `grounding.py`. Angle headlines are templates.
2. **Verify before coding.** Every Qloo parameter and field in the docs is unverified until recorded live in Phase 0 (`docs/qloo-contract.md`, fixtures). Same for Gemma 4 Cloud tool calling (`docs/llm-contract.md`). Never guess parameter names.
3. **Fail closed on Qloo** outside `APP_ENV=test`. The kill switch is a feature.
4. **No local models.** Ollama only as a cloud API with `OLLAMA_API_KEY`. No OpenRouter or other gateways.
5. **Provider isolation.** Only `apps/api/src/tastebound_api/llm/` may name an LLM provider.
6. **Secrets server-side only.** Never logged, traced, returned, committed or bundled. The browser never calls Supabase, Qloo or Ollama.
7. **Respect limits.** Qloo ≤ 4 req/s, per-run and monthly caps; cache as documented.
8. **Tests never touch the network.** Fixtures and respx. Live tests are `@pytest.mark.live` and never run in CI.
9. **Design.** Read `docs/DESIGN.md` before UI work. If it starts with `PLACEHOLDER`, build no screens; build client, types and state only, and tell the user.
10. **Honest copy.** "Taste fit", never "demand" or "will visit". Show arrivals sources. Label templates and inferences.
11. **Scope.** Nothing beyond `docs/01-scope.md` without asking. Stretch only after every MVP criterion passes.

## Working method

- Follow `docs/11-plan.md` phase by phase; verify each phase's gate before moving on.
- Keep `docs/progress.md`: completed tasks, passing acceptance IDs with test names, Qloo calls spent, blockers, questions.
- Small commits referencing acceptance IDs, e.g. `feat(api): baseline lift [MKT-02]`.
- Run `docs/14-checks.md` before each commit.
- When live behaviour differs from the docs: trust live behaviour, update the doc, log the decision in `docs/18-risks-and-decisions.md`.
- Ask only when blocked (keys, design file, demo destination when Phase 0 is inconclusive).
- Before submission, run `docs/judge.md` and save `JUDGING_REPORT.md`.

## Commands

```bash
pnpm install && (cd apps/api && uv sync)
pnpm turbo dev
pnpm turbo lint test build
(cd apps/api && uv run pytest -m "not live")
(cd apps/api && uv run python scripts/export_openapi.py)   # then regenerate packages/contracts
supabase db reset
```

## Conventions

Python typed (mypy strict on `scoring/`, `qloo/`, `agent/`, `arrivals/`, `grounding.py`), Pydantic v2, async httpx. TypeScript strict; API types only from `packages/contracts`. SQL only via migrations. Stable error codes from `docs/07-api-spec.md`.
