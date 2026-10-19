from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

CONFIDENCE_FACTOR = {"high": 1.0, "medium": 0.75, "low": 0.5}


@dataclass
class AllocationInput:
    market_id: str
    city: str
    taste_pct: float
    gap: float | None
    arrivals_pct: float | None
    confidence: str
    locked: bool = False
    locked_amount: float | None = None


@dataclass
class AllocationLine:
    market_id: str
    city: str
    weight: float
    share: float
    amount: float
    locked: bool


def compute_weights(items: list[AllocationInput], mode: str) -> dict[str, float]:
    weights: dict[str, float] = {}
    for item in items:
        factor = CONFIDENCE_FACTOR.get(item.confidence, 0.5)
        if mode == "defend_core":
            weight = item.taste_pct * factor * max(item.arrivals_pct or 0.0, 0.0001)
        else:
            weight = item.taste_pct * factor * (1 + max(item.gap or 0.0, 0.0))
        weights[item.market_id] = max(weight, 0.0001)
    return weights


def _apply_minimum(shares: dict[str, float], minimum: float) -> dict[str, float]:
    if minimum <= 0 or not shares:
        return shares
    count = len(shares)
    if minimum * count >= 1:
        return {key: 1 / count for key in shares}
    adjusted = dict(shares)
    for _ in range(10):
        total = sum(adjusted.values())
        if total <= 0:
            return {key: 1 / count for key in shares}
        adjusted = {key: value / total for key, value in adjusted.items()}
        below = {key for key, value in adjusted.items() if value < minimum}
        if not below:
            break
        for key in below:
            adjusted[key] = minimum
        free = {key: value for key, value in adjusted.items() if key not in below}
        free_total = sum(free.values())
        remaining = 1 - minimum * len(below)
        if free_total <= 0:
            even = remaining / max(len(free), 1)
            adjusted = {key: minimum if key in below else even for key in adjusted}
        else:
            adjusted = {
                key: (minimum if key in below else value / free_total * remaining)
                for key, value in adjusted.items()
            }
    total = sum(adjusted.values())
    return {key: value / total for key, value in adjusted.items()} if total > 0 else adjusted


def allocate(
    items: Iterable[AllocationInput],
    *,
    total: float,
    mode: str = "grow_untapped",
    minimum_share: float = 0.05,
) -> tuple[list[AllocationLine], dict[str, float]]:
    rows = list(items)
    weights = compute_weights(rows, mode)
    locked = [row for row in rows if row.locked and row.locked_amount is not None]
    unlocked = [row for row in rows if not (row.locked and row.locked_amount is not None)]
    locked_total = sum(float(row.locked_amount or 0.0) for row in locked)
    locked_share = min(locked_total / total, 1.0) if total > 0 else 0.0
    unlocked_share_total = max(1.0 - locked_share, 0.0)

    if unlocked:
        weight_total = sum(weights[row.market_id] for row in unlocked)
        raw_shares = {
            row.market_id: (
                (weights[row.market_id] / weight_total) * unlocked_share_total
                if weight_total > 0
                else unlocked_share_total / len(unlocked)
            )
            for row in unlocked
        }
        raw_shares = _apply_minimum(
            raw_shares, minimum_share * unlocked_share_total / max(unlocked_share_total, 1e-9)
        )
    else:
        raw_shares = {}

    for row in locked:
        raw_shares[row.market_id] = float(row.locked_amount or 0.0) / total

    amounts: dict[str, float] = {}
    for row in rows:
        if row.locked and row.locked_amount is not None:
            amounts[row.market_id] = round(float(row.locked_amount), 2)
        else:
            amounts[row.market_id] = round(raw_shares.get(row.market_id, 0.0) * total, 2)
    difference = round(total - sum(amounts.values()), 2)
    if difference and rows:
        top = max(rows, key=lambda row: raw_shares.get(row.market_id, 0.0))
        amounts[top.market_id] = round(amounts[top.market_id] + difference, 2)

    lines = [
        AllocationLine(
            market_id=row.market_id,
            city=row.city,
            weight=round(weights[row.market_id], 4),
            share=round(amounts[row.market_id] / total, 5) if total else 0.0,
            amount=amounts[row.market_id],
            locked=bool(row.locked and row.locked_amount is not None),
        )
        for row in rows
    ]
    lines.sort(key=lambda line: line.amount, reverse=True)
    return lines, weights
