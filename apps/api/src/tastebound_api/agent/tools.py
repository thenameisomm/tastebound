"""
Qloo Tool Definitions for Iterative Agent

This module defines the available Qloo tools that the iterative agent can call.
Each tool has a stable identifier, description, input schema, and execution function.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Awaitable
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class ToolSpec:
    """Specification for a Qloo tool."""
    name: str
    description: str
    input_schema: type[BaseModel]
    execute: Callable[..., Awaitable[dict[str, Any]]]
    output_schema: type[BaseModel] | None = None


# Tool Input Schemas

class SearchEntitiesInput(BaseModel):
    query: str = Field(..., min_length=2, max_length=120, description="Search query")
    entity_type: str = Field(default="place", description="Type of entity to search for")


class GetTasteTagsInput(BaseModel):
    entity_ids: list[str] = Field(..., min_length=1, max_length=20, description="Qloo entity IDs to get tags for")


class GetDemographicsInput(BaseModel):
    entity_ids: list[str] = Field(..., min_length=1, max_length=20, description="Profile entity IDs")
    market_lat: float | None = Field(default=None, ge=-90, le=90, description="Market latitude")
    market_lon: float | None = Field(default=None, ge=-180, le=180, description="Market longitude")


class GetInsightsInput(BaseModel):
    entity_ids: list[str] = Field(..., min_length=1, max_length=20, description="Profile entity IDs")
    market_lat: float = Field(..., ge=-90, le=90, description="Market latitude")
    market_lon: float = Field(..., ge=-180, le=180, description="Market longitude")
    baseline: bool = Field(default=False, description="Whether to query baseline (without destination)")


class GetAudienceInput(BaseModel):
    entity_ids: list[str] = Field(..., min_length=1, max_length=20, description="Profile entity IDs")


class GetPartnersInput(BaseModel):
    entity_ids: list[str] = Field(..., min_length=1, max_length=20, description="Profile entity IDs")
    market_lat: float = Field(..., ge=-90, le=90, description="Market latitude")
    market_lon: float = Field(..., ge=-180, le=180, description="Market longitude")
    partner_type: str = Field(..., description="Type of partner (podcast, artist, movie, book)")


class GetGlobalBrandsInput(BaseModel):
    entity_ids: list[str] = Field(..., min_length=1, max_length=20, description="Profile entity IDs")


# Tool Output Schemas

class SearchEntitiesOutput(BaseModel):
    entities: list[dict[str, Any]]
    call_id: str


class GetTasteTagsOutput(BaseModel):
    tags: list[dict[str, Any]]
    call_id: str


class GetDemographicsOutput(BaseModel):
    available: bool
    rows: list[dict[str, Any]]
    call_ids: list[str]


class GetInsightsOutput(BaseModel):
    target_affinity: float | None
    baseline_affinity: float | None
    contributions: list[dict[str, Any]]
    call_ids: list[str]
    warnings: list[str]


class GetAudienceOutput(BaseModel):
    available: bool
    rows: list[dict[str, Any]]
    call_id: str


class GetPartnersOutput(BaseModel):
    candidates: list[dict[str, Any]]
    call_id: str
    warnings: list[str]


class GetGlobalBrandsOutput(BaseModel):
    brands: list[dict[str, Any]]
    call_id: str
    warnings: list[str]


# Tool registry - will be populated by the executor
TOOL_REGISTRY: dict[str, ToolSpec] = {}

def register_tool(spec: ToolSpec) -> None:
    """Register a tool in the global registry."""
    TOOL_REGISTRY[spec.name] = spec

def get_tool(name: str) -> ToolSpec | None:
    """Get a tool by name."""
    return TOOL_REGISTRY.get(name)

def list_tools() -> list[ToolSpec]:
    """List all registered tools."""
    return list(TOOL_REGISTRY.values())
