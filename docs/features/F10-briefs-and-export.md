# F10. Market briefs and export

**Purpose:** a one-page brief per shortlisted market the marketer can share internally, every claim cited.

## How it works

1. **Evidence bundle per market** (code): taste score, lift, confidence, quadrant, gap, arrivals share and source note, audience summary, angle evidence, top partners per type, budget share, each item with an evidence id.
2. **Write** with the LLM (`market_brief.md`, temperature `LLM_TEMPERATURE_WRITING`). Output schema: `{"title": str, "summary": str ≤ 400 chars, "sections": [{"heading": str, "body": str ≤ 700 chars, "cited_evidence_ids": [str]}]}` with sections: Why this market, Who to target, What to lead with, Partners to approach, Budget and caveats.
3. **Grounding validator** (`grounding.py`): every cited id belongs to this market's bundle; every number in the text appears in the bundle (after formatting tolerance); every proper name (market, destination, partners, entities, tags) appears in the bundle; a caveats sentence ("taste fit, not a visitor forecast") is present.
4. Fail → one regeneration with errors → fallback **template brief** labelled `template`.
5. User can edit the text; edits are saved; evidence chips stay attached.
6. **Export:** Markdown per market (with an evidence appendix listing sources), a print-friendly page, and a CSV of the market table (rank, market, taste score, lift, confidence, arrivals share, gap, quadrant, budget share, angle headline, top partner per type).

## Tests

Validator rejects invented numbers, names, unknown ids, missing caveat; template fallback; edit persistence; CSV columns and UTF-8; Markdown export contains evidence appendix.

Acceptance: BRF-01 to BRF-05, LLM-04, LLM-05.
