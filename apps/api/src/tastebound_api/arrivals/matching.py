from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from tastebound_api.arrivals.parser import ArrivalsInputRow, normalize

CITY_ALIASES = {
    "new york city": "new york",
    "nyc": "new york",
    "washington dc": "washington",
    "washington d c": "washington",
    "sao paulo": "sao paulo",
    "mexico df": "mexico city",
    "ciudad de mexico": "mexico city",
    "lisboa": "lisbon",
    "roma": "rome",
    "milano": "milan",
    "munchen": "munich",
    "wien": "vienna",
    "praha": "prague",
    "warszawa": "warsaw",
    "koln": "cologne",
    "frankfurt am main": "frankfurt",
}


@dataclass
class MarketRef:
    id: str
    city: str
    country_code: str
    country_name: str
    population_band: int


@dataclass
class MatchedArrivals:
    by_market: dict[str, int] = field(default_factory=dict)
    by_country: dict[str, int] = field(default_factory=dict)
    matched_rows: list[dict[str, object]] = field(default_factory=list)
    unmatched_rows: list[dict[str, object]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def matched_market_count(self) -> int:
        return len(self.by_market)


def _split_by_population(total: int, markets: list[MarketRef]) -> dict[str, int]:
    if len(markets) == 1:
        return {markets[0].id: total}
    weights = [max(market.population_band, 1) for market in markets]
    weight_sum = sum(weights)
    raw = [total * weight / weight_sum for weight in weights]
    allocated = [int(value) for value in raw]
    remainder = total - sum(allocated)
    order = sorted(
        range(len(markets)),
        key=lambda index: raw[index] - allocated[index],
        reverse=True,
    )
    for index in order[:remainder]:
        allocated[index] += 1
    return {market.id: allocated[index] for index, market in enumerate(markets)}


def _country_lookup(markets: Iterable[MarketRef]) -> dict[str, str]:
    return {normalize(market.country_name): market.country_code for market in markets}


def match_arrivals(
    rows: Iterable[ArrivalsInputRow],
    markets: list[MarketRef],
) -> MatchedArrivals:
    result = MatchedArrivals()
    by_country: dict[str, list[MarketRef]] = {}
    for market in markets:
        by_country.setdefault(market.country_code, []).append(market)
    country_lookup = _country_lookup(markets)
    city_lookup: dict[str, list[MarketRef]] = {}
    for market in markets:
        key = normalize(market.city)
        city_lookup.setdefault(CITY_ALIASES.get(key, key), []).append(market)

    country_totals: dict[str, int] = {}
    country_rows: list[ArrivalsInputRow] = []
    for row in rows:
        origin = row.origin_raw.strip()
        city_part, _, country_part = origin.partition(",")
        city_key = normalize(city_part or origin)
        city_key = CITY_ALIASES.get(city_key, city_key)
        country_hint = normalize(country_part) if country_part else ""

        if city_key in city_lookup:
            candidates = city_lookup[city_key]
            if country_hint:
                hinted = [
                    market
                    for market in candidates
                    if normalize(market.country_name) == country_hint
                    or normalize(market.country_code) == country_hint
                ]
                candidates = hinted or candidates
            if len(candidates) == 1:
                market = candidates[0]
                result.by_market[market.id] = result.by_market.get(market.id, 0) + row.arrivals
                result.matched_rows.append(
                    {
                        "line": row.line,
                        "origin": origin,
                        "arrivals": row.arrivals,
                        "market_id": market.id,
                        "level": "city",
                    }
                )
                continue

        code = None
        if len(origin) == 2 and origin.isalpha():
            code = origin.upper()
        if code is None:
            code = country_lookup.get(normalize(origin))
        if code is None and country_hint:
            if len(country_part.strip()) == 2 and country_part.strip().isalpha():
                code = country_part.strip().upper()
            else:
                code = country_lookup.get(country_hint)
        if code is None:
            result.unmatched_rows.append(
                {
                    "line": row.line,
                    "origin": origin,
                    "arrivals": row.arrivals,
                    "reason": "No selected market or country matched this origin.",
                }
            )
            continue
        if code not in by_country:
            result.unmatched_rows.append(
                {
                    "line": row.line,
                    "origin": origin,
                    "arrivals": row.arrivals,
                    "reason": f"Country {code} has no selected origin market in this run.",
                }
            )
            continue
        country_totals[code] = country_totals.get(code, 0) + row.arrivals
        country_rows.append(row)
        result.matched_rows.append(
            {
                "line": row.line,
                "origin": origin,
                "arrivals": row.arrivals,
                "country": code,
                "level": "country",
            }
        )

    for code, total in country_totals.items():
        markets_in_country = by_country[code]
        split = _split_by_population(total, markets_in_country)
        for market_id, value in split.items():
            result.by_market[market_id] = result.by_market.get(market_id, 0) + value
        result.by_country[code] = total
    if country_rows:
        result.notes.append(
            "Country-level arrivals were split across the selected markets in that country "
            "by population band. This is an approximation, labelled wherever arrivals appear."
        )
    return result
