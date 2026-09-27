from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import psycopg

from catalog_pipeline.config import load_config
from catalog_pipeline.landing import iter_batches


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_path(path: Path) -> tuple[date, str]:
    ingest_date = None
    entity = None
    for part in path.parts:
        if part.startswith("ingest_date="):
            ingest_date = date.fromisoformat(part.split("=", 1)[1])
        if part.startswith("entity="):
            entity = part.split("=", 1)[1]
    if ingest_date is None or entity is None:
        raise ValueError(f"Cannot parse landing path: {path}")
    return ingest_date, entity


def load_landing() -> dict:
    cfg = load_config(require_database=True)
    inserted = 0
    skipped = 0
    with psycopg.connect(cfg.database_url) as conn:
        for path in iter_batches(cfg.landing_root):
            digest = _hash_file(path)
            ingest_date, entity = _parse_path(path)
            exists = conn.execute(
                "SELECT 1 FROM ops.file_registry WHERE file_hash = %s",
                (digest,),
            ).fetchone()
            if exists:
                skipped += 1
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            rel = str(path)
            with conn.transaction():
                conn.execute(
                    """
                    INSERT INTO bronze.raw_payload (file_hash, path, entity, ingest_date, payload)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (digest, rel, entity, ingest_date, json.dumps(payload)),
                )
                conn.execute(
                    """
                    INSERT INTO ops.file_registry (file_hash, path, entity, ingest_date)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (digest, rel, entity, ingest_date),
                )
            inserted += 1
    return {"inserted": inserted, "skipped": skipped}
