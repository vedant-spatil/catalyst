"""Migrations, then load landing JSON, then transform. No invented roster."""

from __future__ import annotations

import os
import sys
import time
import traceback
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "pipelines"), str(ROOT / "apps" / "api"), str(ROOT)]

from catalog_pipeline.load import load_landing
from catalog_pipeline.transform import transform
from warehouse.apply_migrations import apply_migrations


def wait_db() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Missing environment variable: DATABASE_URL")
    last = None
    for _ in range(30):
        try:
            with psycopg.connect(url, connect_timeout=2) as conn:
                conn.execute("SELECT 1")
            return
        except Exception as exc:
            last = exc
            print(f"waiting for database: {exc}", flush=True)
            time.sleep(1)
    raise SystemExit(f"database not reachable: {last}")


def main() -> None:
    try:
        wait_db()
        print("migrate", apply_migrations(), flush=True)
        print("load", load_landing(), flush=True)
        print("transform", transform(), flush=True)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
