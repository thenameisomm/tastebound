from __future__ import annotations

from pathlib import Path

PROMPT_VERSION = "2026.10.1"
PROMPT_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")
