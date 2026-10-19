from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from tastebound_api.scoring.markets import ScoredMarket, percentile_rank

QUADRANTS = ("untapped", "core", "habit", "low_priority")


@dataclass
class GapResult:
    market_id: str
    arrivals: int
    arrivals_share: float
    arrivals_pct: float
    gap: float
    quadrant: str


def quadrant_for(
    taste_pct: float,
    arrivals_pct: float,
    *,
    taste_threshold: float = 0.5,
    arrivals_threshold: float = 0.5,
) -> str:
    if taste_pct >= taste_threshold and arrivals_pct < arrivals_threshold:
        return "untapped"
    if taste_pct >= taste_threshold and arrivals_pct >= arrivals_threshold:
        return "core"
    if taste_pct < taste_threshold and arrivals_pct >= arrivals_threshold:
        return "habit"
    return "low_priority"


def compute_gap(
    scored: Iterable[ScoredMarket],
    arrivals_by_market: dict[str, int],
    *,
    taste_threshold: float = 0.5,
    arrivals_threshold: float = 0.5,
    minimum_markets: int = 5,
) -> dict[str, GapResult]:
    eligible = {
        row.market_id: row
        for row in scored
        if row.market_id in arrivals_by_market and row.taste_score is not None
    }
    total = sum(arrivals_by_market[market_id] for market_id in eligible)
    if len(eligible) < minimum_markets or total <= 0:
        return {}
    shares = {market_id: arrivals_by_market[market_id] / total for market_id in eligible}
    shares_pct = percentile_rank(shares)
    results: dict[str, GapResult] = {}
    for market_id, row in eligible.items():
        taste_pct = (row.taste_score or 0.0) / 100.0
        arrivals_pct = shares_pct[market_id]
        results[market_id] = GapResult(
            market_id=market_id,
            arrivals=arrivals_by_market[market_id],
            arrivals_share=round(shares[market_id], 5),
            arrivals_pct=round(arrivals_pct, 4),
            gap=round(taste_pct - arrivals_pct, 4),
            quadrant=quadrant_for(
                taste_pct,
                arrivals_pct,
                taste_threshold=taste_threshold,
                arrivals_threshold=arrivals_threshold,
            ),
        )
    return results
