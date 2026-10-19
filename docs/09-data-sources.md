# 09. Data sources

## Qloo (core)

See `04-qloo-integration.md`. All taste data, profiles, scores, audiences, angles and partners.

## Origin market catalogue (`apps/api/src/tastebound_api/data/markets.json`)

- 60–80 major origin cities across regions: city, ISO country code, region, latitude, longitude, radius (default 40 km), population band 1–5.
- Coordinates and population bands entered by hand from a reliable public reference; note the reference in the file header.
- Preset groups: Europe top 20, North America top 15, Asia-Pacific top 15, Middle East top 8, Latin America top 10.
- Phase 0 checks Qloo coverage per city; cities with consistently thin data are marked `active: false` with a note.

## Arrivals data (gap view)

**Preferred: the user's own data.** DMOs usually hold arrivals or overnight stays by origin market. Upload as CSV (`origin, arrivals, year`).

**Demo: one bundled public dataset** for the demo destination, chosen in Phase 0. Requirements:
- Published by an official statistics office or tourism authority, openly licensed or explicitly allowing reuse.
- At least 15 origin markets that overlap the catalogue.
- Stored as `data/samples/<destination>-<year>.csv` with a sidecar `<same>.json`: `{source_name, url, retrieved_on, licence, notes}`.
- The UI shows the source note wherever arrivals appear.

Candidate approach: pick the demo destination where such a dataset is easy to obtain and Qloo coverage is good. Do not scrape sites whose terms forbid it. If no suitable dataset is found, the demo uses a clearly labelled **illustrative** CSV built from published totals, and the README says so.

## Destination websites (intake)

Read only for the signature-item proposal (F01), with SSRF protection, robots.txt respected, 3 pages maximum, text kept 30 days.

## LLM

Ollama Cloud (default) or another direct provider; it supplies no data.

## Licences and attribution

- Respect Qloo's API terms; do not republish raw Qloo data in bulk (exports contain the derived scores and top items only).
- Cite arrivals sources in UI, briefs and README.
- Repository needs an open-source licence (MIT or Apache-2.0) per the hackathon rules.
