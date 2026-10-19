# F09. Budget allocator

**Purpose:** turn the analysis into a spending split the marketer can adjust.

## How it works

1. Inputs: total budget (currency chosen by the user, default USD), shortlisted markets, mode: **Grow untapped** (default) or **Defend core**.
2. Weight per market:
   - Grow untapped: `w = taste_pct × confidence_factor × (1 + max(gap, 0))`
   - Defend core: `w = taste_pct × confidence_factor × arrivals_pct`
   - `confidence_factor`: High 1.0, Medium 0.75, Low 0.5. All provisional and shown in the UI.
3. Shares = w / Σw, rounded to whole currency units with the remainder given to the top market; minimum share per market configurable (default 5%).
4. Sliders let the user set any market manually; the others re-normalise proportionally. Locked markets keep their value.
5. Pure function in `scoring/allocation.py`; runs client-side too for instant feedback, with the server as source of truth on save.

## UI

Plan page: total budget input, mode toggle, one slider per market with amount and share, lock icons, reset.

## Tests

Shares sum exactly to the budget; minimum share respected; lock and re-normalise behaviour; both modes; identical results client and server for the same inputs.

Acceptance: BUD-01 to BUD-03.
