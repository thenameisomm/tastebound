from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

NUMBER_RE = re.compile(r"(?<![\w])(\d+(?:[.,]\d+)?%?)(?![\w])")
WORD_RE = re.compile(r"\b[A-Z][A-Za-zÀ-ÿ'’\-&]*(?:\s+[A-Z][A-Za-zÀ-ÿ'’\-&]*)*\b")

CAVEAT_PATTERNS = (
    re.compile(r"taste fit.{0,40}not a visitor forecast", re.IGNORECASE | re.DOTALL),
    re.compile(r"taste fit.{0,40}not demand", re.IGNORECASE | re.DOTALL),
)

ALLOWED_NAME_WORDS = {
    "a",
    "an",
    "not",
    "no",
    "of",
    "to",
    "so",
    "but",
    "or",
    "per",
    "vs",
    "also",
    "because",
    "however",
    "while",
    "if",
    "then",
    "than",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "on",
    "onto",
    "over",
    "under",
    "about",
    "after",
    "before",
    "during",
    "here",
    "there",
    "when",
    "where",
    "which",
    "who",
    "whose",
    "its",
    "it",
    "is",
    "are",
    "was",
    "were",
    "has",
    "have",
    "had",
    "can",
    "could",
    "should",
    "would",
    "will",
    "may",
    "might",
    "must",
    "our",
    "their",
    "them",
    "why",
    "what",
    "partners",
    "budget",
    "and",
    "caveats",
    "the",
    "this",
    "that",
    "these",
    "those",
    "we",
    "you",
    "they",
    "people",
    "market",
    "markets",
    "destination",
    "qloo",
    "tastebound",
    "lift",
    "taste",
    "score",
    "confidence",
    "arrivals",
    "gap",
    "quadrant",
    "age",
    "gender",
    "female",
    "male",
    "index",
    "share",
    "summary",
    "lead",
    "with",
    "core",
    "untapped",
    "habit",
    "low",
    "priority",
    "high",
    "medium",
    "january",
    "february",
    "march",
    "april",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}


@dataclass
class EvidenceBundle:
    market_id: str
    destination: str
    market_city: str
    evidence_ids: set[str] = field(default_factory=set)
    names: set[str] = field(default_factory=set)
    numbers: set[float] = field(default_factory=set)


@dataclass
class BriefContent:
    title: str
    summary: str
    sections: list[dict[str, Any]]


def _normalise_number(text: str) -> float | None:
    cleaned = text.replace("%", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _number_supported(value: float, bundle: EvidenceBundle) -> bool:
    for candidate in bundle.numbers:
        if abs(candidate - value) <= 0.005:
            return True
        if candidate != 0 and abs((candidate - value) / candidate) <= 0.01:
            return True
        if abs(candidate * 100 - value) <= 0.5 or abs(candidate - value / 100) <= 0.005:
            return True
    return False


def build_bundle(
    *,
    market_id: str,
    destination: str,
    market_city: str,
    evidence: list[dict[str, Any]],
    numbers: list[float],
    names: list[str],
) -> EvidenceBundle:
    bundle = EvidenceBundle(
        market_id=market_id,
        destination=destination,
        market_city=market_city,
    )
    for item in evidence:
        evidence_id = str(item.get("id", "")).strip()
        if evidence_id:
            bundle.evidence_ids.add(evidence_id)
        label = str(item.get("label", "")).strip()
        if label:
            bundle.names.add(label)
        value = item.get("value")
        if isinstance(value, int | float):
            bundle.numbers.add(float(value))
    for number in numbers:
        bundle.numbers.add(float(number))
    for name in names:
        if name:
            bundle.names.add(name)
    bundle.names.add(destination)
    bundle.names.add(market_city)
    return bundle


def validate_brief(content: BriefContent, bundle: EvidenceBundle) -> list[str]:
    violations: list[str] = []
    text = " ".join(
        [content.title, content.summary]
        + [
            f"{section.get('heading', '')} {section.get('body', '')}"
            for section in content.sections
        ]
    )
    for section in content.sections:
        for cited in section.get("cited_evidence_ids", []) or []:
            if cited not in bundle.evidence_ids:
                violations.append(f"Unknown evidence id '{cited}'.")

    known_numbers = {round(number, 6) for number in bundle.numbers}
    for raw in NUMBER_RE.findall(text):
        value = _normalise_number(raw)
        if value is None:
            continue
        if value in known_numbers:
            continue
        if not _number_supported(value, bundle):
            violations.append(f"Number '{raw}' is not in the evidence bundle.")

    allowed = {name.casefold() for name in bundle.names} | ALLOWED_NAME_WORDS
    for match in WORD_RE.findall(text):
        folded = match.casefold()
        if folded in allowed:
            continue
        # Multi-word names with lowercase connectors ("Pastéis de Belém") match in parts;
        # accept any fragment that appears inside an allowed name.
        if any(folded in name for name in allowed):
            continue
        words = match.split()
        if any(word.casefold() in allowed for word in words):
            continue
        violations.append(f"Name '{match}' is not in the evidence bundle.")

    if not any(pattern.search(text) for pattern in CAVEAT_PATTERNS):
        violations.append("Missing the 'taste fit, not a visitor forecast' caveat.")

    return sorted(set(violations))
