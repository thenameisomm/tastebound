from __future__ import annotations

from tastebound_api.qloo.models import QlooEntity
from tastebound_api.qloo.service import (
    DestinationMatch,
    QlooService,
    ResolvedItem,
)


class _StubService(QlooService):
    def __init__(self, entities: list[QlooEntity]) -> None:
        self._entities = entities

    async def search_entities(
        self,
        query: str,
        entity_type: str,
        *,
        run_id: str | None,
        step: str,
        take: int = 10,
    ) -> tuple[list[QlooEntity], str]:
        return self._entities, "call-1"


def _destination() -> DestinationMatch:
    return DestinationMatch(
        query="Toronto",
        name="Toronto",
        entity_id="destination-toronto",
        entity_type="destination",
        lat=43.6532,
        lon=-79.3832,
        country_code="CA",
        country_name="Canada",
        tags=[],
        call_id="call-destination",
    )


def _resolved(
    *,
    item_id: str,
    name: str,
    entity_id: str,
    call_id: str,
) -> ResolvedItem:
    return ResolvedItem(
        item_id=item_id,
        name=name,
        kind="landmark",
        role="requested",
        entity_id=entity_id,
        entity_name=name,
        entity_type="place",
        similarity=1.0,
        status="resolved",
        note=None,
        tags=[
            {
                "id": "tag-1",
                "label": "Architectural history",
                "type": "urn:tag:interests:qloo",
            }
        ],
        call_id=call_id,
    )


async def test_city_locality_is_not_a_signature_item() -> None:
    locality = QlooEntity.model_validate(
        {
            "name": "Toronto",
            "entity_id": "locality-toronto",
            "types": ["urn:entity:locality"],
            "location": {"lat": 43.6532, "lon": -79.3832},
        }
    )
    service = _StubService([locality])

    result = await service.resolve_item(
        item_id="item-1",
        name="Toronto Islands",
        kind="landmark",
        destination=_destination(),
        run_id=None,
    )

    assert result.status == "unresolved"


async def test_specific_place_still_resolves() -> None:
    place = QlooEntity.model_validate(
        {
            "name": "Toronto Islands",
            "entity_id": "place-toronto-islands",
            "types": ["urn:entity:place"],
            "location": {"lat": 43.6205, "lon": -79.3789},
            "properties": {"primary_genre": {"name": "Park"}},
        }
    )
    service = _StubService([place])

    result = await service.resolve_item(
        item_id="item-1",
        name="Toronto Islands",
        kind="landmark",
        destination=_destination(),
        run_id=None,
    )

    assert result.status == "resolved"
    assert result.entity_id == "place-toronto-islands"


def test_build_profile_dedupes_entity_ids() -> None:
    service = _StubService([])
    items = [
        _resolved(item_id="item-1", name="A", entity_id="entity-1", call_id="call-1"),
        _resolved(item_id="item-2", name="B", entity_id="entity-1", call_id="call-2"),
        _resolved(item_id="item-3", name="C", entity_id="entity-2", call_id="call-3"),
    ]

    profile = service.build_profile(destination=_destination(), resolved_items=items)

    assert [item.entity_id for item in profile.entities] == ["entity-1", "entity-2"]
    assert profile.resolved_count == 2
    assert "Merged duplicate profile matches: B" in profile.warnings
    tag = next(item for item in profile.tags if item["label"] == "Architectural history")
    assert tag["count"] == 2
