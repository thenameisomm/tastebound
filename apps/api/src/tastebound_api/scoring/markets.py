from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

SCORING_VERSION = "2026.10.1"
DEFAULT_THRESHOLDS = {
    "gap_taste": 0.5,
    "gap_arrivals": 0.5,
    "population_correlation": 0.6,
    "thin_coverage": 0.5,
}


@dataclass
class MarketObservation:
    market_id: str
    target_affinity: float | None
    baseline_affinity: float | None
    contribution_count: int = 0
    population_band: int = 1
    source_call_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    contributions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ScoredMarket:
    market_id: str
    target_affinity: float | None
    baseline_affinity: float | None
    lift: float | None
    target_pct: float | None
    baseline_pct: float | None
    taste_score: float | None
    coverage: float
    confidence: str
    flags: list[str]
    rank: int | None
    source_call_ids: list[str]
    population_band: int
    warnings: list[str]


def percentile_rank(values: dict[str, float]) -> dict[str, float]:
    """Mid-rank percentile in [0, 1]; ties share a percentile."""
    if not values:
        return {}
    ordered = sorted(values.values())
    count = len(ordered)
    result: dict[str, float] = {}
    for key, value in values.items():
        below = 0
        equal = 0
        for candidate in ordered:
            if candidate < value:
                below += 1
            elif candidate == value:
                equal += 1
        result[key] = (below + 0.5 * equal) / count
    return result


def _confidence(coverage: float, contribution_count: int) -> str:
    if coverage >= 1.0 and contribution_count >= 2:
        return "high"
    if coverage >= 0.5:
        return "medium"
    return "low"


def score_markets(
    observations: Iterable[MarketObservation],
    *,
    thin_coverage: float = DEFAULT_THRESHOLDS["thin_coverage"],
) -> list[ScoredMarket]:
    rows = list(observations)
    valid_lifts = {
        row.market_id: row.target_affinity - row.baseline_affinity
        for row in rows
        if row.target_affinity is not None and row.baseline_affinity is not None
    }
    target_values = {
        row.market_id: row.target_affinity for row in rows if row.target_affinity is not None
    }
    baseline_values = {
        row.market_id: row.baseline_affinity for row in rows if row.baseline_affinity is not None
    }
    target_pct = percentile_rank(target_values)
    baseline_pct = percentile_rank(baseline_values)
    lift_pct = percentile_rank(valid_lifts)

    scored: list[ScoredMarket] = []
    for row in rows:
        lift = valid_lifts.get(row.market_id)
        if row.target_affinity is not None and row.baseline_affinity is not None:
            coverage = 1.0
        elif row.target_affinity is not None or row.baseline_affinity is not None:
            coverage = 0.5
        else:
            coverage = 0.0
        flags: list[str] = []
        if coverage < thin_coverage:
            flags.append("thin_data")
        if row.contribution_count == 0:
            flags.append("no_explainability")
        scored.append(
            ScoredMarket(
                market_id=row.market_id,
                target_affinity=row.target_affinity,
                baseline_affinity=row.baseline_affinity,
                lift=lift,
                target_pct=target_pct.get(row.market_id),
                baseline_pct=baseline_pct.get(row.market_id),
                taste_score=round(lift_pct[row.market_id] * 100, 2)
                if row.market_id in lift_pct
                else None,
                coverage=coverage,
                confidence=_confidence(coverage, row.contribution_count),
                flags=flags,
                rank=None,
                source_call_ids=row.source_call_ids,
                population_band=row.population_band,
                warnings=row.warnings,
            )
        )
    ranked = sorted(
        [row for row in scored if row.taste_score is not None],
        key=lambda row: row.taste_score or 0.0,
        reverse=True,
    )
    for index, ranked_row in enumerate(ranked, start=1):
        ranked_row.rank = index
    return sorted(
        scored,
        key=lambda row: (
            row.taste_score is not None,
            row.taste_score if row.taste_score is not None else -1.0,
        ),
        reverse=True,
    )


def population_correlation(scored: Iterable[ScoredMarket]) -> float | None:
    rows = [row for row in scored if row.lift is not None]
    if len(rows) < 5:
        return None
    xs = [float(row.population_band) for row in rows]
    ys = [float(row.lift or 0.0) for row in rows]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return None
    return numerator / (denom_x * denom_y)
