from __future__ import annotations

from tastebound_api.llm.parsing import extract_json_object


def test_plain_json() -> None:
    assert extract_json_object('{"items": ["a"]}') == {"items": ["a"]}


def test_fenced_json() -> None:
    text = '```json\n{"name": "Lisbon"}\n```'
    assert extract_json_object(text) == {"name": "Lisbon"}


def test_prose_wrapped_json() -> None:
    text = 'Sure! Here is the result: {"ok": true} — enjoy.'
    assert extract_json_object(text) == {"ok": True}


def test_invalid_returns_none() -> None:
    assert extract_json_object("no json here") is None
    assert extract_json_object("{broken") is None
    assert extract_json_object("") is None
    assert extract_json_object(None) is None
    assert extract_json_object("[1, 2]") is None
