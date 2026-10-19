# 00. Product brief

## One line

**TasteBound finds the origin markets whose residents already love what your destination offers but aren't visiting yet, and tells you how to pitch each one.**

## The problem

Destination marketing organisations (DMOs) spend limited public money on campaigns in a handful of origin markets. Their data tools (mobile location, card spend, flight searches, bookings) show **who already comes or already searches**. They cannot show **who would love the destination but hasn't considered it**, so budgets keep chasing the same markets.

- The median destination organisation budget is about **$1.77M** a year, 92% public funding (Destinations International, Mar 8, 2022).
- Brand USA's federal matching funds fell from **$100M to $20M** (PAX News, Jul 4, 2025), so spending smarter per market matters.

Verify these sources again before quoting them in the demo.

## Users

| User | Decision | How often |
|---|---|---|
| **Marketing director at a city or regional DMO** | Which 3–6 origin markets get next year's campaign budget, with what message and media partners | Annual planning plus quarterly reviews |
| Marketing lead at a hotel group or resort | Which feeder markets to target for a property | Quarterly |
| Tourism consultant or agency | Market-entry recommendations for clients | Per project |

## What the user gets

1. A **taste profile** of the destination built from Qloo entities (signature places, food, culture, events), editable.
2. **Market scores** for 20–40 origin cities: taste lift over a popularity baseline, with confidence.
3. A **gap view**: taste lift versus actual arrival share (from the DMO's own arrivals CSV or a public dataset). Markets with high taste fit and low arrivals are **untapped**.
4. Per market: **audience** (age and gender skew from Qloo), **campaign angle** with the Qloo tags and explanations behind it, and **media partners** (podcasts, artists, films, books popular with that market's matching audience).
5. A **budget split** across chosen markets with a live slider.
6. **Market briefs** (one page per market) and a CSV export, every claim traced to a Qloo call.

## Why it is impossible without Qloo

| Output | Source | Without Qloo |
|---|---|---|
| Destination taste profile | Qloo entity search, tags | Generic adjectives |
| Market taste lift | Qloo location-aware insights against a baseline | Nothing: no dataset maps cross-domain taste to origin cities |
| Gap (taste vs arrivals) | Qloo lift minus arrivals share | Only arrivals, which shows existing visitors, not latent fans |
| Audience per market | Qloo demographics | Census data, unrelated to taste |
| Campaign angle evidence | Qloo tags and explanations | LLM guesswork |
| Media partners per market | Qloo cross-domain insights with location | Generic "top podcasts" lists |

With Qloo switched off, the app refuses to score markets (kill switch, tested).

## Positioning

- **Zartico, Datafy, Mabrian, ForwardKeys, Sojern/Adara** measure existing behaviour: visits, spend, searches, bookings. TasteBound measures **latent taste fit** and is a complement, not a replacement: the gap view literally combines the two.
- **Qloo hackathon 2025:** about 343 projects; none targeted tourism boards or origin markets. Travel entries (40+) were consumer itinerary planners. The 2025 grand prize (GeoTaste) analysed a location for a business; TasteBound reverses the direction (destination → origin markets) and adds the arrivals gap.

## Success metrics (hackathon)

| Metric | Target |
|---|---|
| Two different destinations produce clearly different market rankings | Top-10 Jaccard ≤ 0.5 |
| Qloo lift ranking differs from population or arrivals ranking | Spearman with population ≤ 0.6 |
| Backtest: gap markets in year Y−3 grew faster by year Y than non-gap markets | Reported honestly either way |
| Every displayed claim traceable to a Qloo call or the arrivals file | 100% |
| Time from destination input to market table | ≤ 90 s on a warm cache |

## Non-goals

Forecasting visitor numbers, flight routes or prices, booking, personal data, ad buying.
