# 08. Frontend specification (Next.js)

**Read `docs/DESIGN.md` first.** If it begins with `PLACEHOLDER`, build only the API client, generated types, hooks and state; tell the user the design file is missing. Visuals come from `DESIGN.md`; behaviour from this file.

## Screens

| Route                           | Screen               | Must contain                                                                                                                                                                                      |
| ------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/`                             | Landing              | One-line pitch, "Start", "See a sample run", 3-step explainer, limits line ("taste fit, not a visitor forecast")                                                                                  |
| `/start` step 1                 | Destination          | Name, country, optional website                                                                                                                                                                   |
| `/start` step 2                 | Signature items      | Editable chips by kind; origin labels (website / general knowledge / user)                                                                                                                        |
| `/start` step 3                 | Taste profile        | Resolved entities, unresolved list, tag cloud, add-from-Qloo search                                                                                                                               |
| `/start` step 4                 | Markets and arrivals | Preset groups, region filters, search to add, 20–40 selected; arrivals CSV upload or sample; Start                                                                                                |
| `/runs/[id]`                    | Run and results      | Live progress with Qloo call counter → **gap quadrant** + market table; shortlist checkboxes; "Deep dive"                                                                                         |
| `/runs/[id]/markets/[marketId]` | Market detail        | Taste score, lift, coverage, confidence explainer; arrivals and gap; demographic signal chart (currently one destination-level Qloo aggregate); angle with evidence; partners tabs; global brands |
| `/runs/[id]/plan`               | Plan                 | Budget input, mode toggle, sliders with locks; briefs (editable) with evidence chips; exports                                                                                                     |
| `/runs/[id]/trace`              | Trace                | Ordered LLM steps, tool calls, Qloo calls; filters; params collapsed                                                                                                                              |
| `/runs/*` drawer                | Results assistant    | Contextual launcher/button; suggestions; messages; evidence links; follow-ups; unavailable, loading, rate-limit and validation-error states                                                       |
| `/sample`                       | Demo                 | Stored run, read-only, label with date                                                                                                                                                            |

## The two key visuals

1. **Gap quadrant:** x = arrivals share percentile, y = taste score percentile; labelled points; quadrant names (Untapped, Core, Habit, Low priority); hover details; click opens market; keyboard-focusable points with text alternatives; a table equivalent below.
2. **Market table:** rank, market, taste score, lift ("+0.18 vs typical"), coverage, confidence badge (text + colour), arrivals share, gap, quadrant; sortable; filters by region, confidence, quadrant.

Every number has a one-sentence tooltip. Every claim has source chips linking to the trace. Demographic charts are labelled as a directional Qloo aggregate, not per-market census data.

## Results assistant

- Contextual **Ask about this market** on market pages sends that market as the focus; **Ask the run** on results sends no focus. A floating launcher opens the same drawer on any `/runs/*` page.
- The drawer uses `role="dialog"`, focus trap, Escape/backdrop close, body scroll lock and restores focus on close. The composer supports Enter to send and Shift+Enter for a newline.
- Suggested questions come from the API bootstrap. Answers show only evidence returned by the server, linking to `#score`, `#audience`, `#angle`, `#partners`, `#method`, the plan or a trace `?call=` row.
- Conversations are stored in `sessionStorage` under `tb_assistant_conversation:{runId}`; an expired conversation is cleared and the next send starts fresh. Conversation content is not placed in `localStorage`.
- User messages are optimistic. A failed request removes the optimistic message, restores the question and shows the mapped error; prior validated messages remain.
- Required states: bootstrap loading, disabled/no provider, run not ready, hydrating, sending with elapsed seconds, empty history, follow-ups, rate-limited/timeout/unavailable/ungrounded, and message near the character limit.
- The drawer must remain usable at 360 px, respect reduced motion and stay out of print output. See `features/F13-results-assistant.md`.

## States (all required)

Loading skeletons · live progress · partial results with warnings · Qloo failure (full error with code and retry; no partial ranking shown as complete) · LLM unavailable (template briefs labelled) · no arrivals (lift-only view with upload prompt) · thin data markets · empty filters · SSE reconnect · 404 for unknown or other workspaces' runs.

## Data access

`lib/api.ts` (typed by `packages/contracts`; gets/creates the workspace token, stores it in `localStorage` key `tb_ws` inside try/catch, sends `X-Workspace-Token`); `lib/sse.ts` (EventSource with `?token=`, reconnect, typed events). No Supabase client and no keys in the browser.

## Components (add to `packages/ui` when reused)

GapQuadrant, MarketTable, ScoreCell, ConfidenceBadge, SourceChip, EvidenceList, AudienceBars, PartnerTabs, BudgetSliders, BriefEditor, ProgressSteps, CallCounter, TraceTable, EmptyState, ErrorPanel, Banner, AssistantProvider, AssistantDrawer, AssistantButton, AssistantLauncher.

## Quality

Keyboard path through Flow A; visible focus; labels; colour never the only signal; works at 360 px (table becomes cards, quadrant scrolls inside its own container); Lighthouse accessibility ≥ 90 on results and market detail; no layout shift on load. Assistant drawer: keyboard-only open/close/send, focus restoration, live-region status and no horizontal overflow at 360 px.

## Copy rules

"Taste fit", never "demand" or "will visit". Label inferences and templates. Show arrivals source notes wherever arrivals appear.
