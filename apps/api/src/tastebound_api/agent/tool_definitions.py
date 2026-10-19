"""
Qloo Tool Definitions for Iterative Agent

Tool specifications and schemas for the iterative agent's tool calling.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


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


# Tool specifications for LLM
TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "search_entities",
            "description": "Search for Qloo entities (places, landmarks, artists, brands, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "entity_type": {"type": "string", "enum": ["place", "destination", "locality", "artist", "brand", "tag"], "default": "place"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_taste_tags",
            "description": "Get taste tags (affinities) for Qloo entities",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 20}
                },
                "required": ["entity_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_demographics",
            "description": "Get audience demographics for profile entities in a market",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 20},
                    "market_lat": {"type": "number", "minimum": -90, "maximum": 90},
                    "market_lon": {"type": "number", "minimum": -180, "maximum": 180}
                },
                "required": ["entity_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_insights",
            "description": "Get target and baseline affinity insights for a market",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 20},
                    "market_lat": {"type": "number", "minimum": -90, "maximum": 90},
                    "market_lon": {"type": "number", "minimum": -180, "maximum": 180},
                    "baseline": {"type": "boolean", "default": False}
                },
                "required": ["entity_ids", "market_lat", "market_lon"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_audience",
            "description": "Get audience breakdown for profile entities",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 20}
                },
                "required": ["entity_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_partners",
            "description": "Get media partners (podcasts, artists, movies, books) for a market",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 20},
                    "market_lat": {"type": "number", "minimum": -90, "maximum": 90},
                    "market_lon": {"type": "number", "minimum": -180, "maximum": 180},
                    "partner_type": {"type": "string", "enum": ["podcast", "artist", "movie", "book"]}
                },
                "required": ["entity_ids", "market_lat", "market_lon", "partner_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_global_brands",
            "description": "Get global brand partners (location-independent)",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 20}
                },
                "required": ["entity_ids"]
            }
        }
    },
]


ITERATIVE_SYSTEM_PROMPT = """You are a taste intelligence agent for destination marketing. Your job is to build a complete market analysis for a destination using Qloo's taste intelligence API.

You have access to the following tools:
1. search_entities - Search for places, landmarks, artists, brands, etc.
2. get_taste_tags - Get taste tags (affinities) for Qloo entities
3. get_demographics - Get audience demographics for profile entities in a market
4. get_insights - Get target and baseline affinity insights for markets
5. get_audience - Get audience breakdown for profile entities
6. get_partners - Get media partners (podcasts, artists, movies, books) for a market
7. get_global_brands - Get global brand partners

WORKFLOW:
1. First, build the destination profile (search entities, resolve items, get tags)
2. Score all markets (get insights for each market, compute lift, score markets)
3. Compute gaps (if arrivals data available)
4. Deep dive on shortlist (audience, angles, partners)
5. Generate briefs

DECISION RULES:
- You MUST call tools in a logical sequence. Don't skip phases.
- For scoring markets, you need to call get_insights for each market (both target and baseline)
- The deterministic scoring will happen automatically after all insights are gathered
- Don't call the same tool with identical arguments repeatedly
- Stop when all required phases are complete
- Each iteration you can call ONE tool (or multiple if they're independent)
- The system will automatically run deterministic scoring after you've gathered all insights

Current phase: {current_phase}
Completed phases: {completed_phases}
Required phases: {required_phases}
Iteration: {iteration}/{max_iterations}
Tool calls so far: {tool_calls_count}/{max_tool_calls}"""


# Phase definitions
REQUIRED_PHASES = ["profile", "score", "gap", "audience", "angles", "partners", "briefs"]

PHASE_TOOLS = {
    "profile": ["search_entities", "get_taste_tags"],
    "score": ["get_insights"],
    "gap": ["compute_gaps"],  # deterministic
    "audience": ["get_audience"],
    "angles": ["get_angles"],  # deterministic
    "partners": ["get_partners", "get_global_brands"],
    "briefs": ["write_briefs"],  # deterministic + LLM
}
