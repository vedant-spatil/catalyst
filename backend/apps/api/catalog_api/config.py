from __future__ import annotations

from catalog_pipeline.config import load_config


def api_config():
    return load_config(require_database=True)
