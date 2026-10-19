from __future__ import annotations

import asyncio
import json
import statistics

from tastebound_api.db.database import dispose_db, get_session_factory, init_db
from tastebound_api.qloo.client import QlooClient
from tastebound_api.qloo.service import QlooService, load_market_catalogue
from tastebound_api.settings import get_settings

ITEMS = [
    ("Time Out Market", "venue"),
    ("Pastéis de Belém", "dish"),
    ("Jerónimos Monastery", "landmark"),
    ("Alfama", "neighbourhood"),
    ("Fado Em Si Bemol", "music"),
]


def percentile_rank(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values.values())
    n = len(ordered)
    if n == 0:
        return {}
    result: dict[str, float] = {}
    for key, value in values.items():
        below = sum(1 for item in ordered if item < value)
        equal = sum(1 for item in ordered if item == value)
        result[key] = (below + 0.5 * equal) / n
    return result


async def main() -> None:
    settings = get_settings()
    await init_db(settings)
    client = QlooClient(get_session_factory(), settings)
    service = QlooService(client)
    try:
        destination = await service.resolve_destination(
            "Lisbon, Portugal", country_code="PT", run_id=None
        )
        resolved = []
        for index, (name, kind) in enumerate(ITEMS):
            resolved.append(
                await service.resolve_item(
                    item_id=None,
                    name=name,
                    kind=kind,
                    destination=destination,
                    run_id=None,
                    position=index,
                )
            )
        profile = service.build_profile(destination=destination, resolved_items=resolved)
        print("profile", profile.resolved_count, profile.entity_ids)
        catalogue = load_market_catalogue()
        rows: list[dict[str, object]] = []
        for index, (market_id, market) in enumerate(catalogue.items()):
            try:
                insight = await service.destination_insight(
                    destination=destination,
                    profile_entity_ids=profile.entity_ids,
                    market_lat=market["lat"],
                    market_lon=market["lon"],
                    run_id=None,
                    step=f"spike68_{market_id}",
                    include_explainability=False,
                )
            except Exception as exc:
                print("ERROR", market_id, type(exc).__name__, exc)
                continue
            rows.append(
                {
                    "market_id": market_id,
                    "city": market["city"],
                    "country": market["country_code"],
                    "region": market["region"],
                    "population_band": market["population_band"],
                    "target": insight.affinity,
                    "baseline": insight.baseline_affinity,
                }
            )
            if index % 10 == 0:
                print("scored", index + 1, "/", len(catalogue))
        target_values = {
            str(row["market_id"]): float(row["target"]) for row in rows if row["target"] is not None
        }
        baseline_values = {
            str(row["market_id"]): float(row["baseline"])
            for row in rows
            if row["baseline"] is not None
        }
        target_pct = percentile_rank(target_values)
        baseline_pct = percentile_rank(baseline_values)
        for row in rows:
            market_id = str(row["market_id"])
            if market_id in target_pct and market_id in baseline_pct:
                row["lift"] = target_pct[market_id] - baseline_pct[market_id]
        lift_values = {
            str(row["market_id"]): float(row["lift"]) for row in rows if row.get("lift") is not None
        }
        lift_pct = percentile_rank(lift_values)
        for row in rows:
            market_id = str(row["market_id"])
            row["taste_score"] = round(lift_pct.get(market_id, 0) * 100, 1)
        rows.sort(key=lambda row: float(row.get("taste_score", 0)), reverse=True)
        print(json.dumps(rows, indent=2))
        bands = [float(row["population_band"]) for row in rows if row.get("lift") is not None]
        lifts = [float(row["lift"]) for row in rows if row.get("lift") is not None]
        if len(bands) > 2:
            print("population correlation", statistics.correlation(bands, lifts))
        print("scored", len(rows), "of", len(catalogue))
    finally:
        await client.aclose()
        await dispose_db()


if __name__ == "__main__":
    asyncio.run(main())
