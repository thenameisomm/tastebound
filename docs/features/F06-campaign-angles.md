# F06. Campaign angles

**Purpose:** tell the marketer **what to lead with** in each market, backed by Qloo evidence, not marketing intuition.

## How it works

1. For each shortlisted market, find which **profile entities** score highest for that market (from F03 target responses; per-entity percentiles) and which **profile tags** are most shared by the market's top-affinity entities.
2. If Qloo explainability is available (Phase 0), request it for the destination profile against the market and store the returned explanation.
3. Build the **angle evidence** in code: top 3 entities, top 3 tags, and any explanation text, each with source call ids.
4. The **angle headline** is a template: "Lead with {tag1} and {entity1}: people in {market} who like {destination} over-index on them." The LLM does not write the evidence.
5. The brief writer (F10) may phrase the angle more naturally but must cite the evidence ids (grounding validator).
6. Stretch X3: if `/v2/trending` is verified, show entities trending in the market that overlap the profile.

## UI

Market detail: angle headline, evidence list with source chips, "why" popover with raw values.

## Failure handling

No per-entity data for a market → angle "insufficient data", confidence low.

## Tests

Top-entity and tag selection; template output only uses evidence values; evidence ids exist in trace; explainability optional path.

Acceptance: ANG-01 to ANG-04.
