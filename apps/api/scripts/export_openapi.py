from __future__ import annotations

import json
from pathlib import Path

from tastebound_api.main import app

OUTPUT = Path(__file__).resolve().parents[1] / "openapi.json"


def main() -> None:
    spec = app.openapi()
    OUTPUT.write_text(json.dumps(spec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUTPUT} · {len(spec.get('paths', {}))} paths")


if __name__ == "__main__":
    main()
