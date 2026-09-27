from __future__ import annotations

from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from catalog_api.config import api_config


@contextmanager
def get_conn():
    cfg = api_config()
    with psycopg.connect(cfg.database_url, row_factory=dict_row) as conn:
        yield conn
