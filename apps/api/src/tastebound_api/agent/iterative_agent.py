"""
Iterative Qloo Agent - Optional iterative tool-calling layer.

This module provides an iterative agent that can be used when LLM_TOOL_CALLING=true.
It wraps the existing QlooService and provides a tool-calling interface for the LLM.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from tastebound_api.errors import (
    AppError,
    LLMError,
)
from tastebound_api.llm.base import ChatMessage, ToolSpec

from .executor import RunExecutor, _extract_json


@dataclass
class IterationState:
    """Tracks the state of the iterative execution."""
    iteration: int = 0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    last_tool: str | None = None
    last_args: dict[str, Any] | None = None
    repeated_calls: int = 0
    completed_phases: set[str] = field(default_factory=set)
    required_phases: set[str] = field(default_factory=lambda: {
        "profile", "score", "gap", "audience", "angles", "partners", "briefs"
    })


ITERATION_LIMITS = {
    "max_iterations": 25,
    "max_tool_calls": 50,
    "max_repeated_calls": 3,
    "max_llm_calls": 30,
    "max_wall_time_seconds": 300,
}


ITERATIVE_SYSTEM_PROMPT = (
    "You are a taste intelligence agent for destination marketing. "
    "Your job is to build a complete market analysis for a destination "
    "using Qloo's taste intelligence API.\n\n"
    "You have access to the following tools:\n"
    "1. search_entities - Search for places, landmarks, artists, brands, etc.\n"
    "2. get_taste_tags - Get taste tags (affinities) for Qloo entities\n"
    "3. get_demographics - Get audience demographics for profile entities in a market\n"
    "4. get_insights - Get target and baseline affinity insights for markets\n"
    "5. get_audience - Get audience breakdown for profile entities\n"
    "5. get_partners - Get media partners (podcasts, artists, movies, books) for a market\n"
    "7. get_global_brands - Get global brand partners\n\n"
    "WORKFLOW:\n"
    "1. First, build the destination profile (search entities, resolve items, get tags)\n"
    "2. Score all markets (get insights for each market, compute lift, score markets)\n"
    "3. Compute gaps (if arrivals data available)\n"
    "4. Deep dive on shortlist (audience, angles, partners)\n"
    "5. Generate briefs\n\n"
    "DECISION RULES:\n"
    "- You MUST call tools in a logical sequence. Don't skip phases.\n"
    "- For scoring markets, you need to call get_insights for each market "
    "(both target and baseline)\n"
    "- The deterministic scoring will happen automatically after all insights are gathered\n"
    "- Don't call the same tool with identical arguments repeatedly\n"
    "- Stop when all required phases are complete\n"
    "- Each iteration you can call ONE tool (or multiple if they're independent)\n"
    "- The system will automatically run deterministic scoring after you've "
    "gathered all insights\n\n"
    "Current phase: {current_phase}\n"
    "Completed phases: {completed_phases}\n"
    "Required phases: {required_phases}\n"
    "Iteration: {iteration}/{max_iterations}\n"
    "Tool calls so far: {tool_calls_count}/{max_tool_calls}"
)


ITERATIVE_TOOL_SPECS = [
    ToolSpec(
        name="search_entities",
        description="Search for Qloo entities (places, landmarks, artists, brands, etc.)",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "entity_type": {
                "type": "string",
                "enum": ["place", "destination", "locality", "artist", "brand", "tag"],
                "default": "place"
            }
            },
            "required": ["query"]
        }
    ),
    ToolSpec(
        name="get_taste_tags",
        description="Get taste tags (affinities) for Qloo entities",
        parameters={
            "type": "object",
            "properties": {
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 20
                }
            },
            "required": ["entity_ids"]
        }
    ),
    ToolSpec(
        name="get_demographics",
        description="Get audience demographics for profile entities in a market",
        parameters={
            "type": "object",
            "properties": {
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 20
                },
                "market_lat": {"type": "number", "minimum": -90, "maximum": 90},
                "market_lon": {"type": "number", "minimum": -180, "maximum": 180}
            },
            "required": ["entity_ids"]
        }
    ),
    ToolSpec(
        name="get_insights",
        description="Get target and baseline affinity insights for a market",
        parameters={
            "type": "object",
            "properties": {
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 20
                },
                "market_lat": {"type": "number", "minimum": -90, "maximum": 90},
                "market_lon": {"type": "number", "minimum": -180, "maximum": 180},
                "baseline": {"type": "boolean", "default": False}
            },
            "required": ["entity_ids", "market_lat", "market_lon"]
        }
    ),
    ToolSpec(
        name="get_demographics",
        description="Get audience breakdown for profile entities",
        parameters={
            "type": "object",
            "properties": {
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 20
                }
            },
            "required": ["entity_ids"]
        }
    ),
    ToolSpec(
        name="get_partners",
        description="Get media partners (podcasts, artists, movies, books) for a market",
        parameters={
            "type": "object",
            "properties": {
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 20
                },
                "market_lat": {"type": "number", "minimum": -90, "maximum": 90},
                "market_lon": {"type": "number", "minimum": -180, "maximum": 180},
                "partner_type": {"type": "string", "enum": ["podcast", "artist", "movie", "book"]}
            },
            "required": ["entity_ids", "market_lat", "market_lon", "partner_type"]
        }
    ),
    ToolSpec(
        name="get_global_brands",
        description="Get global brand partners (location-independent)",
        parameters={
            "type": "object",
            "properties": {
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 20
                }
            },
            "required": ["entity_ids"]
        }
    ),
]


def _get_current_phase(state: IterationState) -> str:
    if "profile" not in state.completed_phases:
        return "profile"
    elif "score" not in state.completed_phases:
        return "score"
    elif "gap" not in state.completed_phases:
        return "gap"
    elif "audience" not in state.completed_phases or "angles" not in state.completed_phases or "partners" not in state.completed_phases:
        return "deep_dive"
    elif "briefs" not in state.completed_phases:
        return "briefs"
    return "complete"


class IterativeAgent:
    """Iterative Qloo Agent for optional tool-calling execution."""

    def __init__(
        self,
        executor: RunExecutor,
        limits: dict | None = None,
    ) -> None:
        self.executor = executor
        self.limits = limits or ITERATION_LIMITS
        self.state = IterationState()
        self.start_time = time.monotonic()

    def _check_limits(self) -> None:
        """Check if any hard limits have been exceeded."""
        if self.state.iteration >= self.limits["max_iterations"]:
            raise AppError("iteration_limit", 429, "Iteration limit reached",
                f"Maximum {self.limits['max_iterations']} iterations exceeded")
        if len(self.state.tool_calls) >= self.limits["max_tool_calls"]:
            raise AppError("tool_call_limit", 429, "Tool call limit reached",
                f"Maximum {self.limits['max_tool_calls']} tool calls exceeded")
        if self.state.repeated_calls >= self.limits["max_repeated_calls"]:
            raise AppError("repeated_call_limit", 429, "Repeated call limit reached",
                f"Same tool called with same args {self.limits['max_repeated_calls']} times")
        if self.executor.counters["llm"] >= self.limits["max_llm_calls"]:
            raise AppError("llm_call_limit", 429, "LLM call limit reached",
                f"Maximum {self.limits['max_llm_calls']} LLM calls exceeded")
        if time.monotonic() - self.start_time > self.limits["max_wall_time_seconds"]:
            raise AppError("wall_time_limit", 429, "Wall time limit exceeded",
                f"Maximum {self.limits['max_wall_time_seconds']} seconds exceeded")

    def _check_repeated_call(self, tool_name: str, args: dict[str, Any]) -> bool:
        """Check if this tool call is a repeat of the previous one."""
        if self.state.last_tool == tool_name and self.state.last_args == args:
            self.state.repeated_calls += 1
            return True
        self.state.repeated_calls = 0
        return False

    async def _llm_decide_next_action(self) -> tuple[str, dict[str, Any]] | None:
        """Ask the LLM what tool to call next."""
        provider = self.executor.provider
        if provider is None:
            return None

        system = ITERATIVE_SYSTEM_PROMPT.format(
            current_phase=self._get_current_phase(),
            completed_phases=sorted(self.state.completed_phases),
            required_phases=sorted(self.state.required_phases),
            iteration=self.state.iteration,
            max_iterations=self.limits["max_iterations"],
            tool_calls_count=len(self.state.tool_calls),
            max_tool_calls=self.limits["max_tool_calls"],
        )

        messages = [
            ChatMessage(role="system", content=system),
            ChatMessage(
                role="user",
                content="Decide the next tool to call. Return JSON with 'tool' and 'args'.",
            ),
        ]

        self.executor.counters["llm"] += 1
        try:
            result = await self.executor.provider.chat(
                messages,
                temperature=self.executor.settings.llm_temperature_tools,
                response_format={"type": "json_object"},
            )
        except LLMError:
            return None

        parsed = _extract_json(result.content)
        if parsed is None:
            return None

        tool_name = parsed.get("tool")
        args = parsed.get("args", {})

        if not tool_name:
            return None

        return tool_name, args

    def _get_current_phase(self) -> str:
        if "profile" not in self.state.completed_phases:
            return "profile"
        elif "score" not in self.state.completed_phases:
            return "score"
        elif "gap" not in self.state.completed_phases:
            return "gap"
        elif "audience" not in self.state.completed_phases or "angles" not in self.state.completed_phases or "partners" not in self.state.completed_phases:
            return "deep_dive"
        elif "briefs" not in self.state.completed_phases:
            return "briefs"
        return "complete"

    async def _execute_tool(
        self, tool_name: str, args: dict[str, Any], run_id: str
    ) -> dict[str, Any]:
        """Execute an iterative tool by name with given arguments."""
        dispatch = {
            "search_entities": self._search_entities,
            "get_taste_tags": self._get_taste_tags,
            "get_demographics": self._get_demographics,
            "get_insights": self._get_insights,
            "get_audience": self._get_audience,
            "get_partners": self._get_partners,
            "get_global_brands": self._get_global_brands,
        }

        if tool_name not in dispatch:
            raise AppError("unknown_tool", 400, "Unknown tool", f"Tool '{tool_name}' not found")

        if self._check_repeated_call(tool_name, args):
            pass

        self.state.last_tool = tool_name
        self.state.last_args = args

        return await dispatch[tool_name](args, run_id)

    # Tool implementations
    async def _search_entities(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_type = args.get("entity_type", "place")
        entities, call_id = await self.executor.service.search_entities(
            args["query"], entity_type, run_id=run_id, step=f"search_{entity_type}"
        )
        return {"entities": [
            {"entity_id": e.entity_id, "name": e.name, "type": e.type, "tags": [
                {"id": t.id or t.tag_id or "", "label": t.name, "type": t.type or ""}
                for t in e.tags if t.name
            ]} for e in entities
        ], "call_id": call_id}

    async def _get_taste_tags(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_ids = args["entity_ids"]
        all_tags = []
        call_ids = []
        for entity_id in entity_ids:
            tags, call_id = await self.executor.service.get_tags(
                entity_id, run_id=run_id, step=f"tags_{entity_id}"
            )
            all_tags.extend([
                {"entity_id": entity_id, "tag_id": t.tag_id, "name": t.name, "type": t.type}
                for t in tags
            ])
            call_ids.append(call_id)
        return {"tags": all_tags, "call_ids": call_ids}

    async def _get_demographics(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_ids = args["entity_ids"]
        summary = await self.executor.service.demographics(
            profile_entity_ids=entity_ids,
            run_id=run_id,
            step="audience",
        )
        return {"available": summary.available, "rows": summary.rows, "call_ids": summary.call_ids}

    async def _get_insights(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_ids = args["entity_ids"]
        market_lat = args["market_lat"]
        market_lon = args["market_lon"]
        baseline = args.get("baseline", False)

        if self.executor.context.destination_match is None:
            raise AppError("invalid_state", 400, "Destination not resolved")

        insight = await self.executor.service.destination_insight(
            destination=self.executor.context.destination_match,
            profile_entity_ids=entity_ids,
            market_lat=market_lat,
            market_lon=market_lon,
            run_id=run_id,
            step=f"insight_{'baseline' if baseline else 'target'}"
        )
        return {
            "target_affinity": insight.affinity,
            "baseline_affinity": insight.baseline_affinity,
            "contributions": insight.contributions,
            "call_ids": insight.call_ids,
            "warnings": insight.warnings,
        }

    async def _get_audience(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        return await self._get_demographics(args, run_id)

    async def _get_partners(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_ids = args["entity_ids"]
        market_lat = args["market_lat"]
        market_lon = args["market_lon"]
        _ = args["partner_type"]

        candidates, call_id, warnings = await self.executor.service.market_partners(
            profile_entity_ids=entity_ids,
            market_lat=market_lat,
            market_lon=market_lon,
            partner_type=args["partner_type"],
            run_id=run_id,
            step="partners"
        )
        return {
            "candidates": [
                {"entity_id": c.entity.entity_id, "name": c.entity.name, "lift": c.lift, "call_id": c.call_id}
                for c in candidates
            ],
            "call_id": call_id,
            "warnings": warnings,
        }

    async def _get_global_brands(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_ids = args["entity_ids"]
        brands, call_id, warnings = await self.executor.service.global_brands(
            profile_entity_ids=entity_ids,
            run_id=run_id,
            step="global_brands"
        )
        return {
            "brands": [
                {"entity_id": b.entity.entity_id, "name": b.entity.name, "lift": b.lift, "call_id": b.call_id}
                for b in brands
            ],
            "call_id": call_id,
            "warnings": warnings,
        }

    # Phase methods
    async def run_iterative(self, run_id: str) -> None:
        """Run the iterative agent loop."""
        # Phase 1: Build Profile
        await self._profile_phase(run_id)

        # Phase 2: Score Markets
        await self._score_phase(run_id)

        # Phase 3: Compute Gaps
        await self._gap_phase(run_id)

        # Phase 4-6: Deep Dive
        await self._deep_dive_phase(run_id)

        # Phase 7: Write Briefs
        await self._briefs_phase(run_id)

    async def _profile_phase(self, run_id: str) -> None:
        if "profile" in self.state.completed_phases:
            return

        if self.executor.provider is None:
            await self.executor.tool_build_profile()
            self.state.completed_phases.add("profile")
            return

        while "profile" not in self.state.completed_phases:
            self._check_limits()
            self.state.iteration += 1

            action = await self._llm_decide_next_action()
            if action is None:
                break

            tool_name, args = action
            if tool_name not in ("search_entities", "get_taste_tags"):
                break

            result = await self._execute_tool(tool_name, args, run_id)
            self.state.tool_calls.append({"tool": tool_name, "args": args, "result": result})
            self.executor.counters["tools"] += 1

            if self._is_profile_complete():
                self.state.completed_phases.add("profile")
                break

        if "profile" not in self.state.completed_phases:
            await self.executor.tool_build_profile()
            self.state.completed_phases.add("profile")

    def _is_profile_complete(self) -> bool:
        if self.executor.context is None or self.executor.context.destination_match is None:
            return False
        if self.executor.context.profile is None:
            return False
        return self.executor.context.profile.resolved_count >= 3

    async def _score_phase(self, run_id: str) -> None:
        if "score" in self.state.completed_phases:
            return
        await self.executor.tool_score_markets()
        self.state.completed_phases.add("score")

    async def _gap_phase(self, run_id: str) -> None:
        if "gap" in self.state.completed_phases:
            return
        await self.executor.tool_compute_gaps()
        self.state.completed_phases.add("gap")

    async def _deep_dive_phase(self, run_id: str) -> None:
        shortlist = self.executor.context.shortlist if self.executor.context else []
        await self.executor._run_deep_dive_tools(run_id, shortlist)
        self.state.completed_phases.update(["audience", "angles", "partners"])

    async def _briefs_phase(self, run_id: str) -> None:
        if "briefs" in self.state.completed_phases:
            return

        shortlist = self.executor.context.shortlist if self.executor.context else []
        await self.executor.tool_write_briefs(shortlist)
        self.state.completed_phases.add("briefs")

    async def _llm_decide_next_action(self) -> tuple[str, dict[str, Any]] | None:
        provider = self.executor.provider
        if provider is None:
            return None

        system = ITERATIVE_SYSTEM_PROMPT.format(
            current_phase=self._get_current_phase(),
            completed_phases=sorted(self.state.completed_phases),
            required_phases=sorted(self.state.required_phases),
            iteration=self.state.iteration,
            max_iterations=self.limits["max_iterations"],
            tool_calls_count=len(self.state.tool_calls),
            max_tool_calls=self.limits["max_tool_calls"],
        )

        messages = [
            ChatMessage(role="system", content=system),
            ChatMessage(
                role="user",
                content="Decide the next tool to call. Return JSON with 'tool' and 'args'.",
            ),
        ]

        self.executor.counters["llm"] += 1
        try:
            result = await provider.chat(
                messages,
                temperature=self.executor.settings.llm_temperature_tools,
                response_format={"type": "json_object"},
            )
        except LLMError:
            return None

        parsed = _extract_json(result.content)
        if parsed is None:
            return None

        tool_name = parsed.get("tool")
        args = parsed.get("args", {})

        if not tool_name:
            return None

        return tool_name, args

    def _get_current_phase(self) -> str:
        if "profile" not in self.state.completed_phases:
            return "profile"
        elif "score" not in self.state.completed_phases:
            return "score"
        elif "gap" not in self.state.completed_phases:
            return "gap"
        elif "audience" not in self.state.completed_phases or "angles" not in self.state.completed_phases or "partners" not in self.state.completed_phases:
            return "deep_dive"
        elif "briefs" not in self.state.completed_phases:
            return "briefs"
        return "complete"

    async def _execute_tool(
        self, tool_name: str, args: dict[str, Any], run_id: str
    ) -> dict[str, Any]:
        dispatch = {
            "search_entities": self._search_entities,
            "get_taste_tags": self._get_taste_tags,
            "get_demographics": self._get_demographics,
            "get_insights": self._get_insights,
            "get_audience": self._get_audience,
            "get_partners": self._get_partners,
            "get_global_brands": self._get_global_brands,
        }

        if tool_name not in dispatch:
            raise AppError("unknown_tool", 400, "Unknown tool", f"Tool '{tool_name}' not found")

        if self._check_repeated_call(tool_name, args):
            pass

        self.state.last_tool = tool_name
        self.state.last_args = args

        return await dispatch[tool_name](args, run_id)

    def _check_repeated_call(self, tool_name: str, args: dict[str, Any]) -> bool:
        if self.state.last_tool == tool_name and self.state.last_args == args:
            self.state.repeated_calls += 1
            return True
        self.state.repeated_calls = 0
        return False

    async def _check_limits(self) -> None:
        if self.state.iteration >= self.limits["max_iterations"]:
            raise AppError("iteration_limit", 429, "Iteration limit reached",
                f"Maximum {self.limits['max_iterations']} iterations exceeded")
        if len(self.state.tool_calls) >= self.limits["max_tool_calls"]:
            raise AppError("tool_call_limit", 429, "Tool call limit reached",
                f"Maximum {self.limits['max_tool_calls']} tool calls exceeded")
        if self.state.repeated_calls >= self.limits["max_repeated_calls"]:
            raise AppError("repeated_call_limit", 429, "Repeated call limit reached",
                f"Same tool called with same args {self.limits['max_repeated_calls']} times")
        if self.executor.counters["llm"] >= self.limits["max_llm_calls"]:
            raise AppError("llm_call_limit", 429, "LLM call limit reached",
                f"Maximum {self.limits['max_llm_calls']} LLM calls exceeded")
        if time.monotonic() - self.executor.start_time > self.limits["max_wall_time_seconds"]:
            raise AppError("wall_time_limit", 429, "Wall time limit exceeded",
                f"Maximum {self.limits['max_wall_time_seconds']} seconds exceeded")

    def _check_repeated_call(self, tool_name: str, args: dict[str, Any]) -> bool:
        if self.state.last_tool == tool_name and self.state.last_args == args:
            self.state.repeated_calls += 1
            return True
        self.state.repeated_calls = 0
        return False

    # Tool implementations
    async def _search_entities(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_type = args.get("entity_type", "place")
        entities, call_id = await self.executor.service.search_entities(
            args["query"], entity_type, run_id=run_id, step=f"search_{entity_type}"
        )
        return {"entities": [
            {"entity_id": e.entity_id, "name": e.name, "type": e.type, "tags": [
                {"id": t.id or t.tag_id or "", "label": t.name, "type": t.type or ""}
                for t in e.tags if t.name
            ]} for e in entities
        ], "call_id": call_id}

    async def _get_taste_tags(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_ids = args["entity_ids"]
        all_tags = []
        call_ids = []
        for entity_id in entity_ids:
            tags, call_id = await self.executor.service.get_tags(
                entity_id, run_id=run_id, step=f"tags_{entity_id}"
            )
            all_tags.extend([
                {"entity_id": entity_id, "tag_id": t.tag_id, "name": t.name, "type": t.type}
                for t in tags
            ])
            call_ids.append(call_id)
        return {"tags": all_tags, "call_ids": call_ids}

    async def _get_demographics(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_ids = args["entity_ids"]
        summary = await self.executor.service.demographics(
            profile_entity_ids=entity_ids,
            run_id=run_id,
            step="audience",
        )
        return {"available": summary.available, "rows": summary.rows, "call_ids": summary.call_ids}

    async def _get_insights(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_ids = args["entity_ids"]
        market_lat = args["market_lat"]
        market_lon = args["market_lon"]
        baseline = args.get("baseline", False)

        if self.executor.context.destination_match is None:
            raise AppError("invalid_state", 400, "Destination not resolved")

        insight = await self.executor.service.destination_insight(
            destination=self.executor.context.destination_match,
            profile_entity_ids=entity_ids,
            market_lat=market_lat,
            market_lon=market_lon,
            run_id=run_id,
            step=f"insight_{'baseline' if baseline else 'target'}"
        )
        return {
            "target_affinity": insight.affinity,
            "baseline_affinity": insight.baseline_affinity,
            "contributions": insight.contributions,
            "call_ids": insight.call_ids,
            "warnings": insight.warnings,
        }

    async def _get_audience(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        return await self._get_demographics(args, run_id)

    async def _get_partners(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_ids = args["entity_ids"]
        market_lat = args["market_lat"]
        market_lon = args["market_lon"]
        _ = args["partner_type"]

        candidates, call_id, warnings = await self.executor.service.market_partners(
            profile_entity_ids=entity_ids,
            market_lat=market_lat,
            market_lon=market_lon,
            partner_type=args["partner_type"],
            run_id=run_id,
            step="partners"
        )
        return {
            "candidates": [
                {"entity_id": c.entity.entity_id, "name": c.entity.name, "lift": c.lift, "call_id": c.call_id}
                for c in candidates
            ],
            "call_id": call_id,
            "warnings": warnings,
        }

    async def _get_global_brands(self, args: dict[str, Any], run_id: str) -> dict[str, Any]:
        entity_ids = args["entity_ids"]
        brands, call_id, warnings = await self.executor.service.global_brands(
            profile_entity_ids=entity_ids,
            run_id=run_id,
            step="global_brands"
        )
        return {
            "brands": [
                {"entity_id": b.entity.entity_id, "name": b.entity.name, "lift": b.lift, "call_id": b.call_id}
                for b in brands
            ],
            "call_id": call_id,
            "warnings": warnings,
        }
