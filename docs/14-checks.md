# 14. Checks

## Before every commit

- [ ] `uv run ruff check . && uv run ruff format --check . && uv run mypy src` (apps/api)
- [ ] `uv run pytest -m "not live"` passes
- [ ] `pnpm --filter web lint && pnpm --filter web typecheck && pnpm --filter web test`
- [ ] Schema changed → `uv run python scripts/export_openapi.py` and regenerate `packages/contracts`
- [ ] DB changed → new migration file; `supabase db reset` works
- [ ] No keys or `.env` staged
- [ ] Commit message references acceptance IDs, e.g. `feat(api): baseline lift [MKT-02]`

## CI (every push)

API: ruff, mypy, pytest (not live) with coverage, grep tests (LLM-01: provider names only in `llm/`). Web: lint, typecheck, Vitest, `next build`. Contracts diff check. Secret scan (e.g. gitleaks).

## End of each phase

- [ ] Phase acceptance IDs pass and are recorded in `docs/progress.md`
- [ ] Qloo live calls this month noted
- [ ] Docs updated where behaviour changed; decision logged
- [ ] `/sample` still loads

## Daily

- [ ] Qloo usage (SQL in `16-runbook.md`) under 60% before Oct 27
- [ ] Demo run backed up once seeded

## Pre-demo

- [ ] Demo run reseeded with the final scoring version; cache warm
- [ ] `/health` shows `tools_ok: true`
- [ ] Kill-switch rehearsal done and key restored
- [ ] Evaluation numbers ready to quote; arrivals source note visible

## Pre-submit (Oct 29), official requirements

- [ ] Working software integrating the Qloo API
- [ ] Agentic: tool-using agent (F11) explained in README
- [ ] Public repo (GitHub/GitLab/Bitbucket) with open-source `LICENSE`
- [ ] Functional demo link, free and unrestricted, works logged out
- [ ] Text description of features
- [ ] Demo video in English, public
- [ ] Works as shown in the video and text
- [ ] If any earlier code was reused, the submission explains what was built during the period

## Pre-submit, quality

- [ ] Every MVP acceptance criterion passes
- [ ] `docs/judge.md` run; `JUDGING_REPORT.md` saved; top fixes done or noted
- [ ] Clean clone test
- [ ] README: setup, architecture diagram, Qloo chain, kill switch, evaluation, limits, data sources
- [ ] Secret scan clean; bundle has no keys; `pip-audit` and `pnpm audit` reviewed
- [ ] Submitted ≥ 24 hours before the deadline
