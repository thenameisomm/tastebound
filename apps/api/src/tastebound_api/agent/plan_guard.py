from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCORING_ORDER = ["build_profile", "score_markets", "compute_gaps", "finish_phase"]
DEEP_DIVE_TOOLS = ["market_audience", "market_angles", "media_partners"]
DEEP_DIVE_ORDER = [*DEEP_DIVE_TOOLS, "write_briefs", "finish_phase"]
ALLOWED_TOOLS = {"scoring": set(SCORING_ORDER), "deep_dive": set(DEEP_DIVE_ORDER)}


class PlanViolation(Exception):
    pass


@dataclass
class PlanGuard:
    phase: str
    market_ids: set[str] = field(default_factory=set)
    completed: set[str] = field(default_factory=set)
    seen: set[tuple[str, str]] = field(default_factory=set)
    steps: int = 0
    max_steps: int = 12

    def check(self, tool: str, arguments: dict[str, Any]) -> None:
        allowed = ALLOWED_TOOLS.get(self.phase, set())
        if tool not in allowed:
            raise PlanViolation(f"Tool '{tool}' is not allowed in phase '{self.phase}'.")
        if self.steps >= self.max_steps:
            raise PlanViolation(f"Step limit {self.max_steps} reached for phase '{self.phase}'.")
        signature = (tool, repr(sorted(arguments.items())))
        if signature in self.seen:
            raise PlanViolation(f"Identical call to '{tool}' refused.")
        order = SCORING_ORDER if self.phase == "scoring" else DEEP_DIVE_ORDER
        index = order.index(tool)
        missing = [
            name for name in order[:index] if name not in self.completed and name != "finish_phase"
        ]
        if missing:
            raise PlanViolation(f"'{tool}' requires {missing} first.")
        requested = arguments.get("market_ids")
        if requested:
            if not isinstance(requested, list):
                raise PlanViolation("market_ids must be a list.")
            foreign = [market for market in requested if market not in self.market_ids]
            if foreign:
                raise PlanViolation(f"Unknown market ids: {foreign}.")
        if len(str(arguments.get("summary", ""))) > 300:
            raise PlanViolation("finish_phase summary is too long.")

    def record(self, tool: str, arguments: dict[str, Any]) -> None:
        self.seen.add((tool, repr(sorted(arguments.items()))))
        self.steps += 1
        self.completed.add(tool)
