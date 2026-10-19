from __future__ import annotations

import pytest

from tastebound_api.scoring.gap import compute_gap, quadrant_for
from tastebound_api.scoring.markets import (
    MarketObservation,
    percentile_rank,
    population_correlation,
    score_markets,
)


def _obs(market_id: str, target: float, baseline: float, **kwargs: object) -> MarketObservation:
    return MarketObservation(
        market_id=market_id,
        target_affinity=target,
        baseline_affinity=baseline,
        contribution_count=2,
        **kwargs,  # type: ignore[arg-type]
    )


def test_percentile_rank_ties_share_value() -> None:
    ranks = percentile_rank({"a": 1.0, "b": 1.0, "c": 3.0})
    assert ranks["a"] == ranks["b"] == pytest.approx(1 / 3)
    # mid-rank convention: even the maximum keeps half a slot of headroom
    assert ranks["c"] == pytest.approx(2.5 / 3)


def test_lift_reorders_raw_target_affinity() -> None:
    # MKT-02: a market with the highest raw target affinity must lose to one with a bigger lift.
    observations = [
        _obs("big-raw-small-lift", target=0.90, baseline=0.89),
        _obs("small-raw-big-lift", target=0.60, baseline=0.30),
        _obs("middle", target=0.50, baseline=0.45),
    ]
    scored = {row.market_id: row for row in score_markets(observations)}
    small = scored["small-raw-big-lift"]
    big = scored["big-raw-small-lift"]
    assert small.taste_score is not None and small.taste_score > 80.0
    assert big.taste_score is not None and big.taste_score < 20.0
    assert small.rank == 1
    assert big.rank == 3
    # raw target percentile still favours the big market: the lift changed the answer
    assert big.target_pct is not None and small.target_pct is not None
    assert big.target_pct > small.target_pct


def test_thin_data_flag_and_confidence() -> None:
    scored = {row.market_id: row for row in score_markets([_obs("ok", 0.5, 0.4)])}
    assert scored["ok"].flags == []
    assert scored["ok"].confidence == "high"

    missing = score_markets(
        [MarketObservation(market_id="empty", target_affinity=None, baseline_affinity=None)]
    )[0]
    assert "thin_data" in missing.flags
    assert "no_explainability" in missing.flags
    assert missing.coverage == 0.0
    assert missing.taste_score is None
    assert missing.rank is None


def test_population_correlation_detects_size_effect() -> None:
    flat = [
        _obs(f"m{band}", target=0.5, baseline=0.4, population_band=band) for band in range(1, 7)
    ]
    # identical lift at every band: no size signal, correlation is undefined
    assert population_correlation(score_markets(flat)) is None

    growing = [
        _obs(f"m{band}", target=0.1 * band, baseline=0.0, population_band=band)
        for band in range(1, 7)
    ]
    assert (population_correlation(score_markets(growing)) or 0) > 0.9


def test_quadrants() -> None:
    assert quadrant_for(0.9, 0.1) == "untapped"
    assert quadrant_for(0.9, 0.9) == "core"
    assert quadrant_for(0.1, 0.9) == "habit"
    assert quadrant_for(0.1, 0.1) == "low_priority"


def test_gap_requires_minimum_markets_and_matching_arrivals() -> None:
    scored = score_markets(
        [_obs(f"m{index}", target=0.5 + index / 100, baseline=0.4) for index in range(6)]
    )
    arrivals = {f"m{index}": (index + 1) * 100 for index in range(6)}
    gaps = compute_gap(scored, arrivals)
    assert set(gaps) == set(arrivals)
    best_taste = max(gaps.values(), key=lambda row: row.gap)
    assert best_taste.quadrant in {"untapped", "core"}
    assert sum(row.arrivals_share for row in gaps.values()) == pytest.approx(1.0, abs=1e-4)

    assert compute_gap(scored, {"m0": 10}) == {}
