# 15. Evaluation and backtest

Judges ask how thoroughly Qloo is used, and Qloo says a submission that works the same without Qloo is the wrong thing. These checks show whether Qloo changes and improves the market plan. Report results honestly, including where Qloo does not help.

## 1. Sensitivity (does taste change the answer?)

- Two contrasting destinations (from Phase 0), same 30 markets.
- Metric: Jaccard overlap of top-10 markets. **Target ≤ 0.5.** If both destinations get the same top 10, the profile signal is not working.

## 2. Not just size (does lift remove popularity?)

- Spearman correlation between taste score and market population band. **Target ≤ 0.6.**
- Same for the raw target percentile (before baseline). Expect the raw value to correlate more; this shows why the baseline exists.

## 3. Qloo vs no-Qloo

| Setup | Ranking |
|---|---|
| A. TasteBound | Taste lift over baseline |
| B. Arrivals only | Current arrival share (what DMOs already have) |
| C. LLM only | The LLM ranks the same markets from the destination description |

Metrics: top-10 Jaccard A vs B and A vs C (lower = Qloo changes the decision); Spearman on shared markets.

Blind review: for each destination, 10 pairs of markets (one in A's top 10 but not C's, one in C's but not A's); a reviewer with travel-marketing knowledge (or the builder using public interest evidence such as existing direct flights, diaspora, cultural ties) picks which market is the more promising **new** target, without seeing which setup produced it. Report A's wins out of 10.

## 4. Backtest (stretch, needs multi-year arrivals)

If the demo destination has arrivals by origin for year Y−3 and year Y:
1. Compute gaps using Y−3 arrivals and today's taste scores (a limitation: Qloo data is current, not historical; state this).
2. Compare arrivals growth from Y−3 to Y for **Untapped** markets versus the rest.
3. Report median growth for each group and the difference. If untapped markets did not grow faster, say so; the claim becomes "taste-informed shortlist", not "predicts growth".

## Procedure

```bash
uv run python scripts/evaluate.py --destinations <id1>,<id2> --markets preset:europe20,preset:na15 --out ../../docs/evaluation-results.md
uv run python scripts/evaluate.py --score blind_pairs.csv
uv run python scripts/backtest.py --destination <id> --arrivals-old <csv> --arrivals-new <csv> --out ../../docs/evaluation-results.md
```

Results are also saved in the `evaluations` table and quoted in the README and video.

## Limits to state

Small samples; one or two destinations; current taste data against historical arrivals; no causal claim. It shows whether Qloo changes and plausibly improves the shortlist, not whether campaigns will succeed.
