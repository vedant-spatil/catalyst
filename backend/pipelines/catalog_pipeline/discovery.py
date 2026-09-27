from __future__ import annotations

import json

from catalog_pipeline.config import load_config
from catalog_pipeline.spotify_client import SpotifyClient


def _client() -> SpotifyClient:
    cfg = load_config(require_database=False, require_spotify_app=True, require_refresh=True)
    return SpotifyClient(cfg.spotify_client_id, cfg.spotify_client_secret, cfg.spotify_refresh_token)


def list_playlists() -> None:
    client = _client()
    try:
        playlists = client.get_me_playlists()
    finally:
        client.close()
    rows = [{"id": p.get("id"), "name": p.get("name")} for p in playlists]
    print(json.dumps(rows, indent=2))


def search_catalog(query: str) -> None:
    client = _client()
    try:
        body = client.search(query, types="artist", limit=10)
    finally:
        client.close()
    artists = (body.get("artists") or {}).get("items") or []
    rows = [{"id": a.get("id"), "name": a.get("name")} for a in artists]
    print(json.dumps(rows, indent=2))
