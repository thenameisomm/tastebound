from __future__ import annotations

import asyncio
import json

from tastebound_api.db.database import dispose_db, get_session_factory, init_db
from tastebound_api.qloo.client import QlooClient
from tastebound_api.qloo.service import QlooService, load_market_catalogue
from tastebound_api.settings import get_settings


async def main() -> None:
    settings = get_settings()
    await init_db(settings)
    client = QlooClient(get_session_factory(), settings)
    service = QlooService(client)
    try:
        destination = await service.resolve_destination(
            "Lisbon, Portugal", country_code="PT", run_id=None
        )
        print("DESTINATION", json.dumps(destination.__dict__, indent=2, default=str))

        item_specs = [
            ("Time Out Market", "venue"),
            ("Pastéis de Belém", "dish"),
            ("Jerónimos Monastery", "landmark"),
            ("Tram 28", "experience"),
            ("Alfama", "neighbourhood"),
            ("Fado Em Si Bemol", "music"),
        ]
        resolved = []
        for index, (name, kind) in enumerate(item_specs):
            item = await service.resolve_item(
                item_id=None,
                name=name,
                kind=kind,
                destination=destination,
                run_id=None,
                position=index,
            )
            resolved.append(item)
            print(
                "ITEM",
                name,
                "->",
                item.entity_name,
                item.entity_type,
                item.status,
                item.similarity,
            )
        profile = service.build_profile(destination=destination, resolved_items=resolved)
        print(
            "PROFILE",
            "resolved",
            profile.resolved_count,
            "tags",
            [t["label"] for t in profile.tags],
            "unresolved",
            profile.unresolved,
        )

        catalogue = load_market_catalogue()
        for market_id in ["gb-london", "fr-paris", "us-new-york", "jp-tokyo"]:
            market = catalogue[market_id]
            insight = await service.destination_insight(
                destination=destination,
                profile_entity_ids=profile.entity_ids,
                market_lat=market["lat"],
                market_lon=market["lon"],
                run_id=None,
                step=f"spike_{market_id}",
            )
            print(
                "SCORE",
                market_id,
                insight.affinity,
                insight.baseline_affinity,
                "contributions",
                len(insight.contributions),
            )

        partners, _calls, warnings = await service.market_partners(
            profile_entity_ids=profile.entity_ids,
            market_lat=catalogue["gb-london"]["lat"],
            market_lon=catalogue["gb-london"]["lon"],
            partner_type="artist",
            run_id=None,
            step="spike_london",
        )
        print(
            "PARTNERS",
            [(p.entity.name, p.affinity, p.baseline_affinity, p.lift) for p in partners[:8]],
        )
        print("WARNINGS", warnings)

        demographics = await service.demographics(
            profile_entity_ids=profile.entity_ids,
            run_id=None,
            step="spike_london",
            market_lat=catalogue["gb-london"]["lat"],
            market_lon=catalogue["gb-london"]["lon"],
        )
        print("DEMOGRAPHICS", demographics.available, json.dumps(demographics.rows, indent=2))
    finally:
        await client.aclose()
        await dispose_db()


if __name__ == "__main__":
    asyncio.run(main())
