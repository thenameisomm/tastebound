from __future__ import annotations

from tastebound_api.grounding import BriefContent, build_bundle, validate_brief


def _bundle() -> object:
    return build_bundle(
        market_id="jp-tokyo",
        destination="Lisbon",
        market_city="Tokyo",
        evidence=[
            {"id": "ev-1", "label": "Fado", "value": 0.31},
            {"id": "ev-2", "label": "Pastéis de Belém", "value": 0.29},
        ],
        numbers=[99.26, 0.9817, 12.4],
        names=["Fado Em Si Bemol"],
    )


def _content(**overrides: object) -> BriefContent:
    base = {
        "title": "Tokyo: taste-led brief for Lisbon",
        "summary": "Taste fit is 99.26 for Tokyo; this is a taste fit, not a visitor forecast.",
        "sections": [
            {
                "heading": "Why Tokyo",
                "body": "Fado and Pastéis de Belém carry a lift of 0.31. Taste fit, not demand.",
                "cited_evidence_ids": ["ev-1", "ev-2"],
            }
        ],
    }
    base.update(overrides)
    return BriefContent(**base)  # type: ignore[arg-type]


def test_valid_brief_passes() -> None:
    assert validate_brief(_content(), _bundle()) == []


def test_invented_number_is_rejected() -> None:
    violations = validate_brief(_content(summary="Taste fit is 42.42 for Tokyo."), _bundle())
    assert any("42.42" in violation for violation in violations)


def test_unknown_evidence_id_is_rejected() -> None:
    content = _content()
    content.sections[0]["cited_evidence_ids"] = ["ev-1", "ev-ghost"]
    violations = validate_brief(content, _bundle())
    assert any("ev-ghost" in violation for violation in violations)


def test_unknown_name_is_rejected() -> None:
    violations = validate_brief(
        _content(summary="Taste fit is 99.26 and Barcelona loves it, not a visitor forecast."),
        _bundle(),
    )
    assert any("Barcelona" in violation for violation in violations)


def test_missing_caveat_is_rejected() -> None:
    content = _content(
        summary="Taste fit is 99.26 for Tokyo.",
        sections=[
            {
                "heading": "Why Tokyo",
                "body": "Fado carries a lift of 0.31.",
                "cited_evidence_ids": ["ev-1"],
            }
        ],
    )
    violations = validate_brief(content, _bundle())
    assert any("caveat" in violation for violation in violations)


def test_percent_and_scaled_numbers_are_supported() -> None:
    content = _content(summary="Taste fit is 99.26; the gap is 98.17%. Not a visitor forecast.")
    assert validate_brief(content, _bundle()) == []
