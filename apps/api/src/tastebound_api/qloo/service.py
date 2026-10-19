from __future__ import annotations

import json
import math
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

from pydantic import ValidationError

from tastebound_api.errors import (
    DestinationNotFound,
    QlooBadRequest,
    QlooContractViolation,
)
from tastebound_api.qloo.client import QlooClient, QlooResult
from tastebound_api.qloo.models import (
    QlooDemographicBlock,
    QlooDemographicsResponse,
    QlooEntity,
    QlooInsightsResponse,
    QlooSearchResponse,
)
from tastebound_api.settings import API_ROOT

PLACE_KINDS = {"landmark", "venue", "experience", "dish", "drink", "festival", "neighbourhood"}
KIND_TYPES: dict[str, list[str]] = {
    "landmark": ["place", "locality"],
    "venue": ["place"],
    "experience": ["place"],
    "dish": ["place"],
    "drink": ["place"],
    "festival": ["place"],
    "neighbourhood": ["locality", "place"],
    "music": ["artist"],
    "film": ["movie"],
    "book": ["book"],
    "brand": ["brand"],
    "person": ["person"],
}

COUNTRY_NAMES: dict[str, str] = {
    "United Kingdom": "GB",
    "France": "FR",
    "Germany": "DE",
    "Spain": "ES",
    "Italy": "IT",
    "Netherlands": "NL",
    "Austria": "AT",
    "Ireland": "IE",
    "Portugal": "PT",
    "Denmark": "DK",
    "Sweden": "SE",
    "Norway": "NO",
    "Switzerland": "CH",
    "Belgium": "BE",
    "Czechia": "CZ",
    "Czech Republic": "CZ",
    "Poland": "PL",
    "Greece": "GR",
    "United States": "US",
    "Canada": "CA",
    "Mexico": "MX",
    "Japan": "JP",
    "South Korea": "KR",
    "Singapore": "SG",
    "Hong Kong": "HK",
    "Australia": "AU",
    "New Zealand": "NZ",
    "Thailand": "TH",
    "Malaysia": "MY",
    "China": "CN",
    "Taiwan": "TW",
    "India": "IN",
    "United Arab Emirates": "AE",
    "Qatar": "QA",
    "Saudi Arabia": "SA",
    "Israel": "IL",
    "Türkiye": "TR",
    "Turkey": "TR",
    "Oman": "OM",
    "Brazil": "BR",
    "Argentina": "AR",
    "Chile": "CL",
    "Colombia": "CO",
    "Peru": "PE",
    "Panama": "PA",
    "Uruguay": "UY",
    "Ecuador": "EC",
}

LODGING_GENRES = {"lodging", "hotel", "hostel", "serviced accommodation", "apartment", "motel"}
RETAIL_GENRES = {
    "gift shop",
    "souvenir shop",
    "shopping mall",
    "store",
    "furniture store",
    "clothing store",
    "book store",
    "convenience store",
}
FOOD_GENRES = {
    "restaurant",
    "bakery",
    "cafe",
    "coffee shop",
    "bar",
    "food court",
    "market",
    "pastry shop",
    "dessert shop",
    "ice cream shop",
    "seafood restaurant",
    "portuguese restaurant",
    "italian restaurant",
    "mexican restaurant",
    "vegan restaurant",
    "sushi restaurant",
    "hamburger restaurant",
    "family restaurant",
}
TAG_STOPWORDS = {
    "place",
    "destination",
    "tourist attraction",
    "restaurant",
    "bar",
    "cafe",
    "bakery",
    "historic",
    "sightseeing",
    "touristic",
    "walkable",
    "central",
    "scenic",
    "bustling",
    "lively",
    "casual",
    "modern",
    "trendy",
    "vibrant",
    "energetic",
    "fun",
    "social",
    "charming",
    "classic",
    "traditional",
    "authentic",
    "urban",
    "commercial",
    "city center",
    "waterfront",
    "good for kids",
    "wheelchair accessible",
}
TAG_TYPE_PREFIXES = (
    "urn:tag:genre",
    "urn:tag:interests",
    "urn:tag:cuisine",
    "urn:tag:specialty_dish",
    "urn:tag:menu_highlight",
    "urn:tag:culinary_style",
    "urn:tag:dietary_option",
    "urn:tag:customer_identity",
    "urn:tag:ambience",
)

AGE_ORDER = [
    "24_and_younger",
    "25_to_29",
    "30_to_34",
    "35_to_44",
    "45_to_54",
    "55_and_older",
]
GENDER_ORDER = ["female", "male", "other"]
DEMOGRAPHIC_LABELS = {
    "24_and_younger": "Under 25",
    "25_to_29": "25–29",
    "30_to_34": "30–34",
    "35_to_44": "35–44",
    "45_to_54": "45–54",
    "55_and_older": "55+",
    "female": "Female",
    "male": "Male",
    "other": "Other",
}


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    text = text.casefold()
    for char in "-_/&,.'’():":
        text = text.replace(char, " ")
    return " ".join(text.split())


def name_similarity(left: str, right: str) -> float:
    a, b = normalize_name(left), normalize_name(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.92
    return SequenceMatcher(None, a, b).ratio()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _short_type(value: str | None) -> str:
    if not value:
        return ""
    return value.rsplit(":", 1)[-1].lower()


def entity_matches(entity: QlooEntity, expected: Iterable[str]) -> bool:
    actual = {_short_type(value) for value in entity.entity_types}
    return any(value in actual for value in expected)


def _country_code(entity: QlooEntity, fallback: str | None = None) -> str | None:
    properties: dict[str, Any] = entity.properties or {}
    raw_geocode = properties.get("geocode")
    geocode: dict[str, Any] = raw_geocode if isinstance(raw_geocode, dict) else {}
    code = properties.get("country_code") or geocode.get("country_code")
    if isinstance(code, str) and len(code) == 2:
        return code.upper()
    name = properties.get("country") or geocode.get("country")
    if isinstance(name, str):
        return COUNTRY_NAMES.get(name)
    return fallback


def _city_name(entity: QlooEntity) -> str | None:
    properties: dict[str, Any] = entity.properties or {}
    raw_geocode = properties.get("geocode")
    geocode: dict[str, Any] = raw_geocode if isinstance(raw_geocode, dict) else {}
    for value in (geocode.get("city"), properties.get("city"), properties.get("locality")):
        if isinstance(value, str) and value:
            return value
    return None


def _primary_genre(entity: QlooEntity) -> str | None:
    properties: dict[str, Any] = entity.properties or {}
    raw = properties.get("primary_genre")
    if isinstance(raw, dict):
        name = raw.get("name")
        if isinstance(name, str):
            return name
    return None


def place_genre_allowed(kind: str, entity: QlooEntity) -> bool:
    genre = _primary_genre(entity)
    if not genre:
        return True
    lowered = genre.casefold()
    if any(token in lowered for token in LODGING_GENRES):
        return False
    if any(token in lowered for token in RETAIL_GENRES):
        return False
    blocked_food = kind in {"landmark", "experience", "neighbourhood"} and any(
        token in lowered for token in FOOD_GENRES
    )
    return not blocked_food


def tag_is_meaningful(tag: dict[str, str]) -> bool:
    label = tag.get("label", "").strip().casefold()
    if not label or label in TAG_STOPWORDS:
        return False
    tag_type = tag.get("type", "")
    return tag_type.startswith(TAG_TYPE_PREFIXES)


def _tags_from_entity(entity: QlooEntity) -> list[dict[str, str]]:
    return [
        {"id": tag.tag_key, "label": tag.name, "type": tag.type or ""}
        for tag in entity.tags
        if tag.tag_key and tag.name
    ]


def _parse_search(result: QlooResult) -> list[QlooEntity]:
    try:
        parsed = QlooSearchResponse.model_validate(result.data)
    except ValidationError as exc:
        raise QlooContractViolation(f"Unexpected Qloo search shape: {exc.errors()[:2]}") from exc
    return parsed.results


def _parse_insights(result: QlooResult) -> QlooInsightsResponse:
    try:
        return QlooInsightsResponse.model_validate(result.data)
    except ValidationError as exc:
        raise QlooContractViolation(f"Unexpected Qloo insights shape: {exc.errors()[:2]}") from exc


@dataclass
class DestinationMatch:
    query: str
    name: str
    entity_id: str
    entity_type: str
    lat: float | None
    lon: float | None
    country_code: str | None
    country_name: str | None
    tags: list[dict[str, str]]
    call_id: str
    radius_km: int = 40


@dataclass
class ResolvedItem:
    item_id: str | None
    name: str
    kind: str
    role: str
    entity_id: str | None
    entity_name: str | None
    entity_type: str | None
    similarity: float
    status: str
    note: str | None
    tags: list[dict[str, str]] = field(default_factory=list)
    call_id: str | None = None


@dataclass
class ProfileBuild:
    entities: list[ResolvedItem]
    tags: list[dict[str, Any]]
    unresolved: list[str]
    warnings: list[str]
    call_ids: list[str]

    @property
    def resolved_count(self) -> int:
        return len(self.entities)

    @property
    def entity_ids(self) -> list[str]:
        return [item.entity_id for item in self.entities if item.entity_id]


@dataclass
class DestinationInsight:
    affinity: float | None
    baseline_affinity: float | None
    contributions: list[dict[str, Any]]
    explanations: list[str]
    warnings: list[str]
    call_ids: list[str]


@dataclass
class PartnerCandidate:
    partner_type: str
    entity: QlooEntity
    affinity: float
    baseline_affinity: float | None
    lift: float | None
    call_id: str
    market_specific: bool


@dataclass
class DemographicsSummary:
    rows: list[dict[str, Any]]
    call_ids: list[str]
    warnings: list[str]
    available: bool
    baseline_available: bool
    note: str | None = None


class QlooService:
    def __init__(self, client: QlooClient) -> None:
        self.client = client

    async def search_entities(
        self,
        query: str,
        entity_type: str,
        *,
        run_id: str | None,
        step: str,
        take: int = 10,
    ) -> tuple[list[QlooEntity], str]:
        result = await self.client.get(
            "/search",
            {
                "query": query,
                "types": f"urn:entity:{entity_type}",
                "take": take,
            },
            run_id=run_id,
            step=step,
        )
        return _parse_search(result), result.call_id

    async def resolve_destination(
        self,
        name: str,
        *,
        country_code: str | None,
        run_id: str | None,
        step: str = "destination_search",
    ) -> DestinationMatch:
        query_name = name.split(",")[0].strip() or name.strip()
        entities, call_id = await self.search_entities(
            query_name, "destination", run_id=run_id, step=step, take=5
        )
        target = next(
            (
                entity
                for entity in entities
                if entity_matches(entity, ["destination"])
                and name_similarity(query_name, entity.name) >= 0.6
            ),
            None,
        )
        if target is None:
            localities, locality_call = await self.search_entities(
                query_name, "locality", run_id=run_id, step=f"{step}_locality", take=5
            )
            target = next(
                (
                    entity
                    for entity in localities
                    if entity_matches(entity, ["locality"])
                    and name_similarity(query_name, entity.name) >= 0.72
                ),
                None,
            )
            if target is not None:
                call_id = locality_call
        if target is None:
            raise DestinationNotFound(name)

        lat = target.location.lat if target.location else None
        lon = target.location.lon if target.location else None
        properties = target.properties or {}
        resolved_country = _country_code(target, country_code)
        country_name = properties.get("country")
        if not isinstance(country_name, str):
            country_name = None
        return DestinationMatch(
            query=name,
            name=target.name,
            entity_id=target.entity_id,
            entity_type=_short_type(target.subtype or (target.types[0] if target.types else "")),
            lat=lat,
            lon=lon,
            country_code=resolved_country,
            country_name=country_name,
            tags=_tags_from_entity(target),
            call_id=call_id,
        )

    async def resolve_item(
        self,
        *,
        item_id: str | None,
        name: str,
        kind: str,
        destination: DestinationMatch,
        run_id: str | None,
        position: int = 0,
    ) -> ResolvedItem:
        expected_types = KIND_TYPES.get(kind, ["place"])
        attempts = [name]
        if destination.name and normalize_name(destination.name) not in normalize_name(name):
            attempts.append(f"{name}, {destination.name}")

        best: tuple[float, QlooEntity, str] | None = None
        for attempt in attempts:
            for entity_type in expected_types:
                try:
                    entities, call_id = await self.search_entities(
                        attempt,
                        entity_type,
                        run_id=run_id,
                        step=f"profile_item_{position}_{kind}",
                        take=10,
                    )
                except QlooBadRequest:
                    continue
                for entity in entities:
                    if not entity_matches(entity, [entity_type]):
                        continue
                    if entity.entity_id == destination.entity_id:
                        continue
                    if entity_type in {"place", "locality"} and not place_genre_allowed(
                        kind, entity
                    ):
                        continue
                    similarity = name_similarity(attempt, entity.name)
                    if similarity < 0.55:
                        continue
                    dest_lat = destination.lat
                    dest_lon = destination.lon
                    if kind in PLACE_KINDS and dest_lat is not None and dest_lon is not None:
                        location = entity.location
                        if (
                            location is not None
                            and location.lat is not None
                            and location.lon is not None
                        ):
                            distance = haversine_km(
                                dest_lat,
                                dest_lon,
                                location.lat,
                                location.lon,
                            )
                            if distance > max(destination.radius_km, 40) * 1.6:
                                continue
                        city = _city_name(entity)
                        if (
                            city
                            and normalize_name(city) != normalize_name(destination.name)
                            and similarity < 0.9
                        ):
                            continue
                    if best is None or similarity > best[0]:
                        best = (similarity, entity, call_id)
                if best is not None:
                    break
            if best is not None:
                break

        if best is None:
            return ResolvedItem(
                item_id=item_id,
                name=name,
                kind=kind,
                role="requested",
                entity_id=None,
                entity_name=None,
                entity_type=None,
                similarity=0.0,
                status="unresolved",
                note="Qloo found no matching entity in the destination area.",
            )

        similarity, entity, call_id = best
        return ResolvedItem(
            item_id=item_id,
            name=name,
            kind=kind,
            role="requested",
            entity_id=entity.entity_id,
            entity_name=entity.name,
            entity_type=_short_type(entity.subtype or (entity.types[0] if entity.types else "")),
            similarity=round(similarity, 3),
            status="resolved",
            note=None,
            tags=_tags_from_entity(entity),
            call_id=call_id,
        )

    def build_profile(
        self,
        *,
        destination: DestinationMatch,
        resolved_items: list[ResolvedItem],
    ) -> ProfileBuild:
        warnings: list[str] = []
        resolved = [item for item in resolved_items if item.status == "resolved"]
        if len(resolved) < 3:
            warnings.append("Fewer than 3 signature items resolved.")
        tag_counter: Counter[str] = Counter()
        tag_meta: dict[str, dict[str, str]] = {}
        tag_sources: dict[str, set[str]] = {}
        for item in resolved:
            for tag in item.tags:
                if not tag_is_meaningful(tag):
                    continue
                key = tag["label"].strip().casefold()
                tag_counter[key] += 1
                tag_meta.setdefault(key, tag)
                tag_sources.setdefault(key, set()).add("resolved_items")
        for tag in destination.tags:
            key = tag["label"].strip().casefold()
            tag_counter[key] += 2
            tag_meta.setdefault(key, tag)
            tag_sources.setdefault(key, set()).add("destination")

        ranked = [key for key, _ in tag_counter.most_common(10)]
        tags = [
            {
                "id": tag_meta[key]["id"],
                "label": tag_meta[key]["label"],
                "count": tag_counter[key],
                "source": "destination" if "destination" in tag_sources[key] else "resolved_items",
            }
            for key in ranked
        ]
        call_ids = list(
            dict.fromkeys(
                [destination.call_id] + [item.call_id for item in resolved_items if item.call_id]
            )
        )
        does_not_exist = [item.name for item in resolved_items if item.status == "unresolved"]
        return ProfileBuild(
            entities=resolved,
            tags=tags,
            unresolved=does_not_exist,
            warnings=warnings,
            call_ids=call_ids,
        )

    async def destination_insight(
        self,
        *,
        destination: DestinationMatch,
        profile_entity_ids: list[str],
        market_lat: float,
        market_lon: float,
        run_id: str | None,
        step: str,
        include_explainability: bool = True,
    ) -> DestinationInsight:
        warnings: list[str] = []
        call_ids: list[str] = []
        target_params: dict[str, Any] = {
            "filter.type": "urn:entity:destination",
            "filter.results.entities": destination.entity_id,
            "signal.interests.entities": ",".join(profile_entity_ids),
            "signal.location": f"POINT({market_lon} {market_lat})",
            "take": 1,
        }
        if include_explainability:
            target_params["feature.explainability"] = "true"
        target = await self.client.get(
            "/v2/insights", target_params, run_id=run_id, step=f"{step}_target"
        )
        call_ids.append(target.call_id)
        target_entity = self._first_entity(target, expected=["destination"], step=step)
        target_affinity = target_entity.query.affinity if target_entity else None
        contributions: list[dict[str, Any]] = []
        explanations: list[str] = []
        if target_entity:
            contributions, explanations = self._extract_explainability(
                target_entity, profile_entity_ids
            )
        warnings.extend(self._warnings(target))

        baseline = await self.client.get(
            "/v2/insights",
            {
                "filter.type": "urn:entity:destination",
                "filter.results.entities": destination.entity_id,
                "signal.location": f"POINT({market_lon} {market_lat})",
                "take": 1,
            },
            run_id=run_id,
            step=f"{step}_baseline",
        )
        call_ids.append(baseline.call_id)
        baseline_entity = self._first_entity(baseline, expected=["destination"], step=step)
        baseline_affinity = baseline_entity.query.affinity if baseline_entity else None
        warnings.extend(self._warnings(baseline))
        return DestinationInsight(
            affinity=target_affinity,
            baseline_affinity=baseline_affinity,
            contributions=contributions,
            explanations=explanations,
            warnings=list(dict.fromkeys(warnings)),
            call_ids=call_ids,
        )

    async def market_partners(
        self,
        *,
        profile_entity_ids: list[str],
        market_lat: float,
        market_lon: float,
        partner_type: str,
        run_id: str | None,
        step: str,
        take: int = 10,
    ) -> tuple[list[PartnerCandidate], list[str], list[str]]:
        call_ids: list[str] = []
        warnings: list[str] = []
        params = {
            "filter.type": f"urn:entity:{partner_type}",
            "signal.interests.entities": ",".join(profile_entity_ids),
            "signal.location": f"POINT({market_lon} {market_lat})",
            "take": take,
        }
        try:
            target = await self.client.get(
                "/v2/insights", params, run_id=run_id, step=f"{step}_{partner_type}_target"
            )
            target_entities = _parse_insights(target)
            target_ids = [
                entity.entity_id
                for entity in target_entities.results.entities
                if entity_matches(entity, [partner_type])
            ][:50]
            if not target_ids:
                warnings.append(f"{partner_type}: no target entities returned")
                return [], [target.call_id], warnings
            baseline = await self.client.get(
                "/v2/insights",
                {
                    "filter.type": f"urn:entity:{partner_type}",
                    "filter.results.entities": ",".join(target_ids),
                    "signal.location": f"POINT({market_lon} {market_lat})",
                    "take": len(target_ids),
                },
                run_id=run_id,
                step=f"{step}_{partner_type}_baseline",
            )
        except QlooBadRequest as exc:
            warnings.append(f"{partner_type}: {exc.detail}")
            return [], call_ids, warnings
        call_ids.extend([target.call_id, baseline.call_id])
        baseline_entities = _parse_insights(baseline)
        if not target_entities.results.entities:
            warnings.append(f"{partner_type}: no target entities returned")
        baseline_by_id = {
            entity.entity_id: entity.query.affinity
            for entity in baseline_entities.results.entities
            if entity.query.affinity is not None
        }
        candidates: list[PartnerCandidate] = []
        for entity in target_entities.results.entities:
            if not entity_matches(entity, [partner_type]):
                continue
            affinity = entity.query.affinity
            if affinity is None:
                continue
            baseline_affinity = baseline_by_id.get(entity.entity_id)
            lift = affinity - baseline_affinity if baseline_affinity is not None else None
            candidates.append(
                PartnerCandidate(
                    partner_type=partner_type,
                    entity=entity,
                    affinity=affinity,
                    baseline_affinity=baseline_affinity,
                    lift=lift,
                    call_id=target.call_id,
                    market_specific=True,
                )
            )
        warnings.extend(self._warnings(target))
        warnings.extend(self._warnings(baseline))
        candidates.sort(
            key=lambda candidate: (
                candidate.lift is not None,
                candidate.lift if candidate.lift is not None else -1.0,
                candidate.affinity,
            ),
            reverse=True,
        )
        return candidates, call_ids, list(dict.fromkeys(warnings))

    async def global_brands(
        self,
        *,
        profile_entity_ids: list[str],
        run_id: str | None,
        step: str,
        take: int = 10,
    ) -> tuple[list[PartnerCandidate], str | None, list[str]]:
        try:
            result = await self.client.get(
                "/v2/insights",
                {
                    "filter.type": "urn:entity:brand",
                    "signal.interests.entities": ",".join(profile_entity_ids),
                    "take": take,
                },
                run_id=run_id,
                step=f"{step}_brands",
            )
        except QlooBadRequest as exc:
            return [], None, [f"brands: {exc.detail}"]
        parsed = _parse_insights(result)
        candidates = [
            PartnerCandidate(
                partner_type="brand",
                entity=entity,
                affinity=entity.query.affinity or 0.0,
                baseline_affinity=None,
                lift=None,
                call_id=result.call_id,
                market_specific=False,
            )
            for entity in parsed.results.entities
            if entity_matches(entity, ["brand"]) and entity.query.affinity is not None
        ]
        return candidates, result.call_id, self._warnings(result)

    async def demographics(
        self,
        *,
        profile_entity_ids: list[str],
        run_id: str | None,
        step: str,
        market_lat: float | None = None,
        market_lon: float | None = None,
    ) -> DemographicsSummary:
        if not profile_entity_ids:
            return DemographicsSummary([], [], [], False, False, "No resolved profile entities.")
        params: dict[str, Any] = {
            "filter.type": "urn:demographics",
            "signal.interests.entities": ",".join(profile_entity_ids[:15]),
        }
        if market_lat is not None and market_lon is not None:
            params["signal.location"] = f"POINT({market_lon} {market_lat})"
        try:
            result = await self.client.get(
                "/v2/insights", params, run_id=run_id, step=f"{step}_demographics"
            )
        except QlooBadRequest as exc:
            return DemographicsSummary([], [], [f"demographics: {exc.detail}"], False, False, None)
        try:
            parsed = QlooDemographicsResponse.model_validate(result.data)
        except ValidationError as exc:
            raise QlooContractViolation(
                f"Unexpected Qloo demographics shape: {exc.errors()[:2]}"
            ) from exc
        blocks = parsed.results.demographics
        if not blocks:
            return DemographicsSummary(
                [], [result.call_id], self._warnings(result), False, False, None
            )
        rows = self._aggregate_demographics(blocks)
        for row in rows:
            row["source_call_id"] = result.call_id
        return DemographicsSummary(
            rows=rows,
            call_ids=[result.call_id],
            warnings=self._warnings(result),
            available=True,
            baseline_available=False,
            note=(
                "Qloo demographics are affinity deltas versus the population average. "
                "A location-only baseline is not supported by this API."
            ),
        )

    def _aggregate_demographics(self, blocks: list[QlooDemographicBlock]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for dimension, order in (("age", AGE_ORDER), ("gender", GENDER_ORDER)):
            values: dict[str, float] = {}
            count = 0
            for block in blocks:
                series = block.query.get(dimension, {})
                if not isinstance(series, dict) or not series:
                    continue
                count += 1
                for band, value in series.items():
                    if isinstance(value, int | float):
                        values[band] = values.get(band, 0.0) + float(value)
            if not values:
                continue
            bands = [band for band in order if band in values] + [
                band for band in values if band not in order
            ]
            for band in bands:
                mean = values[band] / max(count, 1)
                rows.append(
                    {
                        "dimension": dimension,
                        "band": band,
                        "label": DEMOGRAPHIC_LABELS.get(band, band.replace("_", " ")),
                        "share": None,
                        "baseline_share": None,
                        "over_index": round(mean * 100, 1),
                        "raw_affinity": round(mean, 4),
                    }
                )
        return rows

    def _first_entity(
        self,
        result: QlooResult,
        *,
        expected: list[str],
        step: str,
    ) -> QlooEntity | None:
        parsed = _parse_insights(result)
        for entity in parsed.results.entities:
            if entity_matches(entity, expected):
                return entity
        if parsed.results.entities:
            raise QlooContractViolation(f"{step}: Qloo returned an entity of an unexpected type")
        return None

    def _extract_explainability(
        self, entity: QlooEntity, profile_entity_ids: list[str]
    ) -> tuple[list[dict[str, Any]], list[str]]:
        explanation = entity.query.explainability or {}
        rows: list[dict[str, Any]] = []
        texts: list[str] = []

        def walk(value: Any) -> None:
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        entity_id = item.get("entity_id") or item.get("id")
                        score = item.get("score") or item.get("affinity")
                        if entity_id and isinstance(score, int | float):
                            rows.append(
                                {
                                    "entity_id": entity_id,
                                    "score": float(score),
                                    "why": item.get("explanation") or item.get("why"),
                                }
                            )
                        text = item.get("explanation")
                        if isinstance(text, str) and text:
                            texts.append(text)
                    elif isinstance(item, list | dict):
                        walk(item)
            elif isinstance(value, dict):
                for nested in value.values():
                    walk(nested)

        walk(explanation)
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for row in sorted(rows, key=lambda item: item["score"], reverse=True):
            if row["entity_id"] in seen:
                continue
            seen.add(row["entity_id"])
            unique.append(row)
        if not unique and profile_entity_ids:
            unique = []
        return unique[:10], list(dict.fromkeys(texts))[:5]

    @staticmethod
    def _warnings(result: QlooResult) -> list[str]:
        warnings: list[str] = []
        for warning in result.warnings:
            if isinstance(warning, str):
                warnings.append(warning)
            elif isinstance(warning, dict):
                message = warning.get("message") or warning.get("detail")
                if isinstance(message, str):
                    warnings.append(message)
        return warnings


def load_market_catalogue() -> dict[str, dict[str, Any]]:
    path = API_ROOT / "src/tastebound_api/data/markets.json"
    payload = json.loads(path.read_text())
    return {row["id"]: row for row in payload["markets"]}
