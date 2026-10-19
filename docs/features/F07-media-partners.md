# F07. Media partners per market

**Purpose:** suggest **podcasts, artists, films and books** that the destination's would-be fans in each market over-index on, as sponsorship, collaboration or content-placement targets. This is Qloo's cross-domain strength.

## How it works

1. For each shortlisted market and each type (`podcast`, `artist`, `movie`, `book`): Qloo insights with `filter.type` = that type, `signal.interests.entities` = profile entities, `signal.location` = market. Take the top 10.
2. Baseline per type and market (no taste signal) to compute lift; rank partners by lift, not raw popularity, so the list isn't just national chart-toppers.
3. Brands: one global query (brands ignore location), shown separately as "global brand affinities".
4. Store partners with type, lift, rank and source call ids. Explanations attached when available.

## UI

Market detail: four tabs (Podcasts, Artists, Films, Books) with lift badges and "why" chips; a separate global brands list with a note that brands are not market-specific.

## Failure handling

A type with no results shows an empty state for that tab; other tabs unaffected.

## Tests

Lift ranking differs from raw ranking on a crafted fixture; brands never sent with location; empty-tab state; trace links.

Acceptance: PAR-01 to PAR-04.
