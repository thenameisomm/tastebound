# TasteBound web

Next.js App Router frontend for TasteBound. It renders the landing page, intake wizard, live run results, market briefs, budget planner and trace. All Qloo and LLM access happens in `apps/api`; the browser never receives service keys.

```bash
pnpm --filter web dev        # http://localhost:3000
pnpm --filter web lint
pnpm --filter web check-types
pnpm --filter web build
```

Point the app at the API with `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`). Open `/sample` for the keyless demo.

See the root [`README.md`](../../README.md), [`docs/08-frontend-spec.md`](../../docs/08-frontend-spec.md) and [`docs/DESIGN.md`](../../docs/DESIGN.md).
