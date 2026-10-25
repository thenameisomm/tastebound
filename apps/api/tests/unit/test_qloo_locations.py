from __future__ import annotations

from tastebound_api.qloo.models import QlooEntity
from tastebound_api.qloo.service import location_payload


def test_location_payload_maps_place_geocode() -> None:
    entity = QlooEntity.model_validate(
        {
            "name": "Lisbon Cathedral",
            "entity_id": "place-1",
            "types": ["urn:entity:place"],
            "location": {"lat": 38.7098339, "lon": -9.1329535},
            "properties": {
                "geocode": {
                    "country_code": "pt",
                    "country": "Portugal",
                    "city": "Lisbon",
                    "admin2_region": "Lisbon",
                }
            },
            "tags": [{"id": "tag-1", "name": "Cathedral", "type": "urn:tag:genre:place"}],
        }
    )

    payload = location_payload(entity, "place")

    assert payload is not None
    assert payload["id"] == "place-1"
    assert payload["entity_id"] == "place-1"
    assert payload["name"] == "Lisbon Cathedral"
    assert payload["countryCode"] == "PT"
    assert payload["countryName"] == "Portugal"
    assert payload["region"] == "Lisbon"
    assert payload["lat"] == 38.7098339
    assert payload["lon"] == -9.1329535
    assert payload["type"] == "place"
    assert payload["tags"] == [{"id": "tag-1", "label": "Cathedral", "type": "urn:tag:genre:place"}]


def test_location_payload_maps_destination_country() -> None:
    entity = QlooEntity.model_validate(
        {
            "name": "Lisbon",
            "entity_id": "destination-1",
            "types": ["urn:entity:destination"],
            "location": {"lat": 38.7261, "lon": -9.1394},
            "properties": {"country": "Portugal"},
        }
    )

    payload = location_payload(entity, "destination")

    assert payload is not None
    assert payload["name"] == "Lisbon"
    assert payload["countryCode"] == "PT"
    assert payload["countryName"] == "Portugal"
    assert payload["region"] == ""
    assert payload["type"] == "destination"


def test_location_payload_returns_none_without_coordinates() -> None:
    entity = QlooEntity.model_validate(
        {
            "name": "Lisbon",
            "entity_id": "destination-1",
            "types": ["urn:entity:destination"],
            "properties": {"country": "Portugal"},
        }
    )

    assert location_payload(entity, "destination") is None
