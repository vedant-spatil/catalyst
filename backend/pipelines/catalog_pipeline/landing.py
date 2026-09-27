from __future__ import annotations

import json
from pathlib import Path


def write_batch(root: Path, ingest_date: str, entity: str, payload: list[object]) -> Path:
    directory = root / "spotify" / f"ingest_date={ingest_date}" / f"entity={entity}"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "batch.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def iter_batches(root: Path) -> list[Path]:
    base = root / "spotify"
    if not base.exists():
        return []
    return sorted(base.glob("ingest_date=*/entity=*/batch.json"))
