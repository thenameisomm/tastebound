from __future__ import annotations

import pytest

from tastebound_api.arrivals.matching import MarketRef, match_arrivals
from tastebound_api.arrivals.parser import ArrivalsInvalid, normalize, parse_arrivals_csv

MARKETS = [
    MarketRef(
        id="es-madrid", city="Madrid", country_code="ES", country_name="Spain", population_band=5
    ),
    MarketRef(
        id="es-barcelona",
        city="Barcelona",
        country_code="ES",
        country_name="Spain",
        population_band=4,
    ),
    MarketRef(
        id="pt-lisbon", city="Lisbon", country_code="PT", country_name="Portugal", population_band=3
    ),
    MarketRef(
        id="fr-paris", city="Paris", country_code="FR", country_name="France", population_band=6
    ),
    MarketRef(
        id="us-new-york",
        city="New York",
        country_code="US",
        country_name="United States",
        population_band=6,
    ),
]


def test_parse_csv_accepts_headers_and_reports_bad_rows() -> None:
    parsed = parse_arrivals_csv(
        "origin,arrivals,year\nLisboa,1200,2024\n,90,2024\nParis,not-a-number,2024\n,,\n"
    )
    assert [row.origin_raw for row in parsed.rows] == ["Lisboa"]
    assert len(parsed.errors) == 2


def test_parse_csv_requires_columns() -> None:
    with pytest.raises(ArrivalsInvalid):
        parse_arrivals_csv("city,total\nLisbon,1\n")
    with pytest.raises(ArrivalsInvalid):
        parse_arrivals_csv("origin,arrivals\n")


def test_normalize_strips_accents_and_case() -> None:
    assert normalize("São Paulo") == "sao paulo"
    assert normalize("New-York") == "new york"


def test_city_alias_and_country_split() -> None:
    parsed = parse_arrivals_csv("origin,arrivals\nLisboa,300\nSpain,900\n")
    matched = match_arrivals(parsed.rows, MARKETS)
    assert matched.by_market["pt-lisbon"] == 300
    # Spain has no city row: the country total is split across Madrid and Barcelona by band
    assert matched.by_market["es-madrid"] + matched.by_market["es-barcelona"] == 900
    assert matched.by_market["es-madrid"] > matched.by_market["es-barcelona"]
    assert matched.by_country["ES"] == 900
    assert matched.notes and "population band" in matched.notes[0]


def test_country_code_row_and_unmatched_reason() -> None:
    parsed = parse_arrivals_csv("origin,arrivals\nFR,400\nAtlantis,50\n")
    matched = match_arrivals(parsed.rows, MARKETS)
    assert matched.by_market["fr-paris"] == 400
    assert matched.matched_market_count == 1
    assert len(matched.unmatched_rows) == 1
    assert "No selected market" in str(matched.unmatched_rows[0]["reason"])


def test_country_without_selected_market_is_unmatched() -> None:
    parsed = parse_arrivals_csv("origin,arrivals\nDE,700\n")
    matched = match_arrivals(parsed.rows, MARKETS)
    assert matched.by_market == {}
    assert "no selected origin market" in str(matched.unmatched_rows[0]["reason"])
