# F04. Arrivals import and gap analysis

**Purpose:** combine taste fit with **actual visitor arrivals** to find **untapped markets**: high taste fit, low arrivals. This is the product's headline insight.

## Arrivals input

- CSV upload with header `origin, arrivals, year` (origin = city name or ISO country code), up to 500 rows, UTF-8.
- Or a **bundled public sample** for the demo destination in `data/samples/` with its source URL, licence and date in a sidecar JSON (see `09-data-sources.md`).
- Arrivals are stored per workspace as an `arrivals_dataset` with `source_note`.

## Matching

1. Country codes match all markets in that country; arrivals are then split across that country's markets in the run by population band weights (documented, labelled as an approximation) or, if the user prefers, the gap view switches to **country level** (aggregate market scores per country by mean taste score).
2. City names match markets by normalised name plus country.
3. Unmatched rows are listed; unmatched markets show "no arrivals data".

## Gap computation (code only)

- `arrivals_share` = arrivals for the market ÷ total matched arrivals.
- `arrivals_pct` = percentile of arrivals share across matched markets.
- `gap` = `taste_pct − arrivals_pct` (−1 to 1).
- Quadrants (threshold 0.5 each, configurable): **Untapped** (taste ≥ 0.5, arrivals < 0.5), **Core** (≥, ≥), **Habit** (taste < 0.5, arrivals ≥ 0.5), **Low priority** (<, <).
- Each market stores its quadrant and gap; the run stores thresholds.

## UI

**Gap quadrant chart** (x = arrivals share percentile, y = taste score percentile), one labelled point per market, quadrant labels, hover for details, click to open the market. Below it, the table sorted by gap.

## Failure handling

Invalid CSV rows reported with line numbers; valid rows kept; fewer than 5 matched markets → gap view disabled with a notice.

## Tests

CSV parsing (BOM, commas in names, bad numbers); matching by city and country; country-split approximation labelled; gap maths and quadrant boundaries; disabled state under 5 matches; sample dataset loads with source note.

Acceptance: GAP-01 to GAP-05.
