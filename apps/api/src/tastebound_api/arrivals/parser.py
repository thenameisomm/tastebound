from __future__ import annotations

import csv
import io
import unicodedata
from dataclasses import dataclass, field

from tastebound_api.errors import ArrivalsInvalid

MAX_ROWS = 500


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(text.casefold().replace("-", " ").replace("_", " ").split())


@dataclass
class ArrivalsInputRow:
    line: int
    origin_raw: str
    arrivals: int
    year: int | None


@dataclass
class RowError:
    line: int
    message: str
    raw: str | None = None


@dataclass
class ParsedArrivals:
    rows: list[ArrivalsInputRow] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)


def parse_arrivals_csv(content: bytes | str) -> ParsedArrivals:
    if isinstance(content, bytes):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ArrivalsInvalid("The file must be UTF-8 encoded CSV.") from exc
    else:
        text = content.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ArrivalsInvalid("The CSV has no header row. Expected origin, arrivals, year.")
    normalized_headers = {normalize(name): name for name in reader.fieldnames if name}
    origin_header = normalized_headers.get("origin")
    arrivals_header = normalized_headers.get("arrivals")
    year_header = normalized_headers.get("year")
    if not origin_header or not arrivals_header:
        raise ArrivalsInvalid("The CSV must include 'origin' and 'arrivals' columns.")
    parsed = ParsedArrivals()
    for line_number, raw in enumerate(reader, start=2):
        origin = (raw.get(origin_header) or "").strip()
        arrivals_raw = (raw.get(arrivals_header) or "").strip()
        year_raw = (raw.get(year_header) or "").strip() if year_header else ""
        if not origin and not arrivals_raw:
            continue
        if len(parsed.rows) >= MAX_ROWS:
            parsed.errors.append(
                RowError(line_number, f"File exceeds the {MAX_ROWS}-row limit.", None)
            )
            break
        if not origin:
            parsed.errors.append(RowError(line_number, "Origin is empty.", arrivals_raw))
            continue
        try:
            arrivals = int(arrivals_raw.replace(",", "").replace(" ", ""))
        except ValueError:
            parsed.errors.append(
                RowError(
                    line_number,
                    f"Arrivals must be a whole number, got '{arrivals_raw}'.",
                    arrivals_raw,
                )
            )
            continue
        if arrivals < 0:
            parsed.errors.append(
                RowError(line_number, "Arrivals cannot be negative.", arrivals_raw)
            )
            continue
        year: int | None = None
        if year_raw:
            try:
                year = int(year_raw)
            except ValueError:
                parsed.errors.append(
                    RowError(line_number, f"Year must be a number, got '{year_raw}'.", year_raw)
                )
                continue
        parsed.rows.append(
            ArrivalsInputRow(line=line_number, origin_raw=origin, arrivals=arrivals, year=year)
        )
    if not parsed.rows:
        detail = "No valid rows found."
        if parsed.errors:
            detail = f"No valid rows found. First error: {parsed.errors[0].message}"
        raise ArrivalsInvalid(detail)
    return parsed
