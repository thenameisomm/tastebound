from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from tastebound_api.assistant.context import AssistantContext
from tastebound_api.grounding import ALLOWED_NAME_WORDS, NUMBER_RE, WORD_RE

EXTRA_ALLOWED_WORDS = {
    "across",
    "add",
    "additionally",
    "already",
    "although",
    "among",
    "another",
    "answer",
    "ask",
    "balanced",
    "based",
    "best",
    "better",
    "between",
    "both",
    "brand",
    "brands",
    "brief",
    "budget",
    "build",
    "campaign",
    "caveat",
    "caveats",
    "check",
    "choose",
    "city",
    "clear",
    "compare",
    "consider",
    "consumer",
    "core",
    "country",
    "cta",
    "currently",
    "data",
    "despite",
    "different",
    "direct",
    "do",
    "does",
    "don't",
    "each",
    "either",
    "evidence",
    "explain",
    "few",
    "finally",
    "financial",
    "first",
    "fit",
    "focus",
    "forecast",
    "gap",
    "given",
    "go",
    "good",
    "great",
    "here",
    "high",
    "highest",
    "how",
    "however",
    "index",
    "investment",
    "it's",
    "just",
    "lead",
    "leads",
    "least",
    "less",
    "lift",
    "likely",
    "look",
    "low",
    "lower",
    "many",
    "marketing",
    "may",
    "meanwhile",
    "medium",
    "more",
    "most",
    "much",
    "neither",
    "next",
    "no",
    "not",
    "notably",
    "note",
    "now",
    "number",
    "one",
    "only",
    "open",
    "opportunity",
    "other",
    "overall",
    "partner",
    "partners",
    "people",
    "percent",
    "percentage",
    "point",
    "points",
    "pick",
    "plan",
    "please",
    "prioritise",
    "prioritize",
    "priority",
    "read",
    "recommend",
    "recommendation",
    "recommended",
    "remember",
    "risk",
    "riskier",
    "roi",
    "run",
    "same",
    "say",
    "score",
    "scores",
    "second",
    "see",
    "several",
    "shortlist",
    "should",
    "show",
    "signal",
    "signals",
    "since",
    "so",
    "some",
    "start",
    "still",
    "strong",
    "strongest",
    "stronger",
    "such",
    "suggest",
    "suggested",
    "support",
    "target",
    "targeting",
    "test",
    "than",
    "that's",
    "the",
    "therefore",
    "their",
    "then",
    "there",
    "these",
    "they",
    "third",
    "this",
    "those",
    "though",
    "three",
    "thus",
    "to",
    "today",
    "top",
    "treat",
    "two",
    "under",
    "unknown",
    "use",
    "using",
    "value",
    "very",
    "visit",
    "visitor",
    "volume",
    "warm",
    "watch",
    "weak",
    "weakest",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "why",
    "with",
    "within",
    "without",
    "work",
    "would",
    "yes",
    "yet",
    "you",
    "your",
}

ALLOWED_WORDS = set(ALLOWED_NAME_WORDS) | EXTRA_ALLOWED_WORDS


@dataclass
class AssistantDraft:
    answer: str
    evidence_ids: list[str]
    followups: list[str]


def _extract_json(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _number_supported(value: float, numbers: set[float]) -> bool:
    for candidate in numbers:
        if abs(candidate - value) <= 0.005:
            return True
        if candidate != 0 and abs((candidate - value) / candidate) <= 0.01:
            return True
        if abs(candidate * 100 - value) <= 0.5 or abs(candidate - value / 100) <= 0.005:
            return True
    return False


def _word_allowed(raw: str, names: set[str]) -> bool:
    folded = raw.casefold().strip("'’")
    base = re.split(r"['’]", folded, maxsplit=1)[0]
    if folded in names or base in names:
        return True
    words = [word.strip("'’") for word in re.split(r"[\s\-]+", folded) if word]
    return bool(words) and all(word in ALLOWED_WORDS or word in names for word in words)


def parse_draft(raw: str | None) -> tuple[AssistantDraft | None, list[str]]:
    parsed = _extract_json(raw)
    if parsed is None:
        return None, ["The provider did not return a JSON object."]
    answer = str(parsed.get("answer") or "").strip()
    evidence_ids = parsed.get("evidence_ids")
    followups = parsed.get("followups", [])
    if not answer:
        return None, ["The answer is empty."]
    if len(answer) > 1800:
        return None, ["The answer is longer than 1800 characters."]
    if not isinstance(evidence_ids, list) or not evidence_ids:
        return None, ["The answer must cite at least one evidence id."]
    cleaned_ids: list[str] = []
    for item in evidence_ids:
        value = str(item).strip()
        if value and value not in cleaned_ids:
            cleaned_ids.append(value)
    if not cleaned_ids:
        return None, ["The answer must cite at least one evidence id."]
    if len(cleaned_ids) > 6:
        return None, ["Cite at most six evidence ids."]
    cleaned_followups: list[str] = []
    if isinstance(followups, list):
        for item in followups:
            value = str(item).strip()
            if value and len(value) <= 160 and value not in cleaned_followups:
                cleaned_followups.append(value)
    return (
        AssistantDraft(
            answer=answer,
            evidence_ids=cleaned_ids,
            followups=cleaned_followups[:3],
        ),
        [],
    )


def validate_draft(draft: AssistantDraft, context: AssistantContext) -> list[str]:
    violations: list[str] = []
    for evidence_id in draft.evidence_ids:
        if evidence_id not in context.evidence:
            violations.append(f"Unknown evidence id '{evidence_id}'.")

    for raw in NUMBER_RE.findall(draft.answer):
        cleaned = raw.replace("%", "").replace(",", ".").strip()
        try:
            value = float(cleaned)
        except ValueError:
            continue
        if not _number_supported(value, context.numbers):
            violations.append(f"Number '{raw}' is not in this run's data.")

    for match in WORD_RE.findall(draft.answer):
        if not _word_allowed(match, context.names):
            violations.append(f"Name '{match}' is not in this run's data.")

    return sorted(set(violations))
