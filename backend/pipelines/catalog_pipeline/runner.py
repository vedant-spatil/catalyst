from __future__ import annotations

from datetime import date

import psycopg
from psycopg.types.json import Json

from catalog_pipeline.config import load_config
from catalog_pipeline.extract import extract
from catalog_pipeline.load import load_landing
from catalog_pipeline.transform import transform
from warehouse.apply_migrations import apply_migrations


def _log_run(conn, command: str, status: str, snapshot_date, row_counts, error_list) -> None:
    conn.execute(
        """
        INSERT INTO ops.run_log (status, command, snapshot_date, row_counts, error_list, finished_at)
        VALUES (%s, %s, %s, %s, %s, now())
        """,
        (status, command, snapshot_date, Json(row_counts), Json(error_list)),
    )


def run() -> None:
    cfg = load_config(require_database=True, require_spotify_app=True, require_refresh=True)
    apply_migrations(cfg.database_url)
    errors: list = []
    snapshot = date.today()
    try:
        extracted = extract()
        errors.extend(extracted.get("errors") or [])
        snapshot = date.fromisoformat(extracted["ingest_date"])
        loaded = load_landing()
        transformed = transform(snapshot)
        with psycopg.connect(cfg.database_url) as conn:
            _log_run(conn, "run", "success", snapshot, {**loaded, **transformed}, errors)
            conn.commit()
    except Exception as exc:
        with psycopg.connect(cfg.database_url) as conn:
            _log_run(conn, "run", "failed", snapshot, {}, [{"error": type(exc).__name__}])
            conn.commit()
        raise
