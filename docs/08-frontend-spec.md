# 08. Frontend specification (Next.js)

**Read `docs/DESIGN.md` first.** If it begins with `PLACEHOLDER`, build only the API client, generated types, hooks and state; tell the user the design file is missing. Visuals come from `DESIGN.md`; behaviour from this file.

## Screens

| Route | Screen | Must contain |
|---|---|---|
| `/` | Landing | One-line pitch, "Start", "See a sample run", 3-step explainer, limits line ("taste fit, not a visitor forecast") |
| `/start` step 1 | Destination | Name, country, optional website |
| `/start` step 2 | Signature items | Editable chips by kind; origin labels (website / general knowledge / user) |
| `/start` step 3 | Taste profile | Resolved entities, unresolved list, tag cloud, add-from-Qloo search |
| `/start` step 4 | Markets and arrivals | Preset groups, region filters, search to add, 20–40 selected; arrivals CSV upload or sample; Start |
| `/runs/[id]` | Run and results | Live progress with Qloo call counter → **gap quadrant** + market table; shortlist checkboxes; "Deep dive" |
| `/runs/[id]/markets/[marketId]` | Market detail | Taste score, lift, coverage, confidence explainer; arrivals and gap; audience chart; angle with evidence; partners tabs; global brands |
| `/runs/[id]/plan` | Plan | Budget input, mode toggle, sliders with locks; briefs (editable) with evidence chips; exports |
| `/runs/[id]/trace` | Trace | Ordered LLM steps, tool calls, Qloo calls; filters; params collapsed |
| `/sample` | Demo | Stored run, read-only, label with date |

## The two key visuals

1. **Gap quadrant:** x = arrivals share percentile, y = taste score percentile; labelled points; quadrant names (Untapped, Core, Habit, Low priority); hover details; click opens market; keyboard-focusable points with text alternatives; a table equivalent below.
2. **Market table:** rank, market, taste score, lift ("+0.18 vs typical"), coverage, confidence badge (text + colour), arrivals share, gap, quadrant; sortable; filters by region, confidence, quadrant.

Every number has a one-sentence tooltip. Every claim has source chips linking to the trace.

## States (all required)

Loading skeletons · live progress · partial results with warnings · Qloo failure (full error with code and retry; no partial ranking shown as complete) · LLM unavailable (template briefs labelled) · no arrivals (lift-only view with upload prompt) · thin data markets · empty filters · SSE reconnect · 404 for unknown or other workspaces' runs.

## Data access

`lib/api.ts` (typed by `packages/contracts`; gets/creates the workspace token, stores it in `localStorage` key `tb_ws` inside try/catch, sends `X-Workspace-Token`); `lib/sse.ts` (EventSource with `?token=`, reconnect, typed events). No Supabase client and no keys in the browser.

## Components (add to `packages/ui` when reused)

GapQuadrant, MarketTable, ScoreCell, ConfidenceBadge, SourceChip, EvidenceList, AudienceBars, PartnerTabs, BudgetSliders, BriefEditor, ProgressSteps, CallCounter, TraceTable, EmptyState, ErrorPanel, Banner.

## Quality

Keyboard path through Flow A; visible focus; labels; colour never the only signal; works at 360 px (table becomes cards, quadrant scrolls inside its own container); Lighthouse accessibility ≥ 90 on results and market detail; no layout shift on load.

## Copy rules

"Taste fit", never "demand" or "will visit". Label inferences and templates. Show arrivals source notes wherever arrivals appear.
