from __future__ import annotations

import json
from typing import Any, cast

from tastebound_api.assistant.context import AssistantContext
from tastebound_api.assistant.models import EvidenceItem
from tastebound_api.assistant.validation import parse_draft, validate_draft


def _context() -> AssistantContext:
    return AssistantContext(
        run=cast(Any, None),
        destination_name="Lisbon",
        focus_market_id=None,
        payload={},
        evidence={
            "E1": EvidenceItem(
                id="E1",
                kind="market_score",
                label="Cartagena score",
                detail="rank 1 · taste 99.26 · gap 98.17 points",
                href="/runs/demo/markets/co-cartagena#score",
            )
        },
        suggested_questions=[],
        numbers={99.26, 98.17},
        names={"lisbon", "cartagena", "tastebound"},
        ready=True,
    )


def _draft(answer: str, evidence: list[str] | None = None):
    parsed, violations = parse_draft(
        json.dumps(
            {
                "answer": answer,
                "evidence_ids": evidence or ["E1"],
                "followups": ["What supports this?"],
            }
        )
    )
    assert parsed is not None
    assert violations == []
    return parsed


def test_accepts_numbers_and_names_present_in_context() -> None:
    draft = _draft(
        "Cartagena has a taste score of 99.26 and a gap of 98.17 points. "
        "That is taste fit, not a visitor forecast."
    )
    assert validate_draft(draft, _context()) == []


def test_accepts_rounded_and_percentage_forms() -> None:
    draft = _draft("Cartagena scores 99.3, with a gap of 98.2 points.")
    assert validate_draft(draft, _context()) == []


def test_accepts_common_sentence_words() -> None:
    draft = _draft(
        "Please note that Cartagena has a taste score of 99.26. Finally, the gap is 98.17 points."
    )
    assert validate_draft(draft, _context()) == []


def test_rejects_an_invented_number() -> None:
    draft = _draft("Cartagena has a taste score of 12.34.")
    violations = validate_draft(draft, _context())
    assert any("Number '12.34'" in violation for violation in violations)


def test_rejects_an_invented_name() -> None:
    draft = _draft("Paris is the strongest opportunity.")
    violations = validate_draft(draft, _context())
    assert any("Name 'Paris'" in violation for violation in violations)


def test_rejects_unknown_evidence() -> None:
    draft = _draft("Cartagena leads with 99.26.", evidence=["E99"])
    violations = validate_draft(draft, _context())
    assert violations == ["Unknown evidence id 'E99'."]


def test_repairs_fenced_json_and_drops_long_followups() -> None:
    raw = (
        "```json\n"
        + json.dumps(
            {
                "answer": "Cartagena leads with 99.26.",
                "evidence_ids": ["E1"],
                "followups": ["ok", "x" * 161, "ok"],
            }
        )
        + "\n```"
    )
    draft, violations = parse_draft(raw)
    assert violations == []
    assert draft is not None
    assert draft.evidence_ids == ["E1"]
    assert draft.followups == ["ok"]
