from __future__ import annotations

import os

import psycopg
import pytest
from dotenv import load_dotenv

load_dotenv()


def db_available() -> bool:
    url = os.environ.get("DATABASE_URL")
    if not url:
        return False
    try:
        with psycopg.connect(url, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not db_available(), reason="Postgres is not reachable")
