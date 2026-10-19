# CLAUDE.md

Follow `AGENTS.md`; all rules apply. Claude Code specifics:

- Start each session by reading `AGENTS.md`, `docs/progress.md` and the current phase in `docs/11-plan.md`.
- Keep a task list per phase; mark a task done only when its acceptance IDs pass and are recorded.
- Make small, reviewable changes; run `pnpm turbo lint test` and `uv run pytest -m "not live"` before saying a task is done; report failures plainly.
- Live Qloo or Ollama calls only through `apps/api/scripts/`; report how many Qloo calls you spent.
- Never print secrets or `.env` values.
- Never edit generated `packages/contracts`; regenerate.
- Never change an applied migration; add a new one.
- When blocked, stop and ask with a short list of options.
- After each phase, summarise in under 10 lines: what works, IDs passing, what's next, what you need.
- When asked to judge the project, follow `docs/judge.md` and spawn its sub-agents.
