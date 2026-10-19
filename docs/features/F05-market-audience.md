# F05. Market audience

**Purpose:** for each shortlisted market, show **who** in that market over-indexes on the destination's taste (age bands, gender skew), so the campaign targets the right people.

## How it works

1. For each shortlisted market (3–6), call Qloo demographics (`urn:demographics` insight type or `/v2/audiences`, whichever Phase 0 verifies) with the profile entities as signal and the market as location.
2. Also call it without the taste signal for the same market (baseline) if the API supports location-only demographics; report **over-index** per age band = target share − baseline share. If not supported, show target shares and label "no baseline available".
3. Store bands, shares, over-index and source call ids.

## UI

Market detail: small bar chart of age bands with over-index markers; gender split; a one-line template summary ("25–34 over-indexes most (+9 pts)").

## Failure handling

Missing demographics → section shows "Qloo returned no audience data for this market"; never estimated by the LLM.

## Tests

Over-index maths; missing-baseline labelling; contract test with fixtures; UI empty state.

Acceptance: AUD-01 to AUD-03.
