# F08. Competitor positioning (stretch)

**Purpose:** show what the destination offers that a rival destination doesn't, in the eyes of a given market.

## How it works

1. The user picks a rival destination (for example Barcelona vs Lisbon). The rival goes through F01–F02 in a light mode (items proposed by the LLM, resolved by Qloo, user can skip editing).
2. Call `/v2/analysis/compare` between the two profiles (verify parameters in Phase 0), optionally with a market location.
3. Show the entities and tags that most distinguish our destination, as "positioning angles", with evidence.

## UI

Plan page: "Compare with a rival" panel with two columns of distinguishing tags and entities.

## Tests

Contract test for compare; UI hidden unless enabled; evidence ids exist.

Acceptance: CMP-01 to CMP-02 (Stretch).
