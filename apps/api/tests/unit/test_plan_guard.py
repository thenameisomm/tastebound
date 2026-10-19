from __future__ import annotations

import pytest

from tastebound_api.agent.plan_guard import PlanGuard, PlanViolation


def _guard(**overrides: object) -> PlanGuard:
    defaults: dict[str, object] = {
        "phase": "scoring",
        "market_ids": {"jp-tokyo", "co-cartagena"},
    }
    defaults.update(overrides)
    return PlanGuard(**defaults)  # type: ignore[arg-type]


def test_out_of_order_tool_is_refused() -> None:
    guard = _guard()
    with pytest.raises(PlanViolation, match="requires"):
        guard.check("score_markets", {})


def test_order_is_enforced_and_recorded() -> None:
    guard = _guard()
    guard.check("build_profile", {})
    guard.record("build_profile", {})
    guard.check("score_markets", {"market_ids": ["jp-tokyo"]})
    guard.record("score_markets", {"market_ids": ["jp-tokyo"]})
    guard.check("compute_gaps", {})
    guard.record("compute_gaps", {})
    guard.check("finish_phase", {"summary": "done"})
    assert guard.completed == {"build_profile", "score_markets", "compute_gaps"}


def test_duplicate_call_is_refused() -> None:
    guard = _guard()
    guard.check("build_profile", {})
    guard.record("build_profile", {})
    with pytest.raises(PlanViolation, match="Identical"):
        guard.check("build_profile", {})


def test_unknown_market_is_refused() -> None:
    guard = _guard()
    guard.check("build_profile", {})
    guard.record("build_profile", {})
    with pytest.raises(PlanViolation, match="Unknown market"):
        guard.check("score_markets", {"market_ids": ["us-miami"]})


def test_step_limit_and_long_summary() -> None:
    guard = _guard(max_steps=0)
    with pytest.raises(PlanViolation, match="Step limit"):
        guard.check("build_profile", {})

    guard = _guard()
    guard.check("build_profile", {})
    guard.record("build_profile", {})
    guard.check("score_markets", {})
    guard.record("score_markets", {})
    guard.check("compute_gaps", {})
    guard.record("compute_gaps", {})
    with pytest.raises(PlanViolation, match="too long"):
        guard.check("finish_phase", {"summary": "x" * 301})


def test_tool_not_allowed_in_phase() -> None:
    guard = _guard(phase="deep_dive", market_ids={"jp-tokyo"})
    with pytest.raises(PlanViolation, match="not allowed"):
        guard.check("build_profile", {})
