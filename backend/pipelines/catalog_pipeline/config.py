"""Load env. Print missing key names only. Never print values."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Config:
    database_url: str
    landing_root: Path
    spotify_client_id: str
    spotify_client_secret: str
    spotify_refresh_token: str
    spotify_redirect_uri: str
    api_port: int
    web_origin: str
    watchlist_path: Path


def missing_env(keys: list[str]) -> list[str]:
    load_dotenv(ROOT / ".env")
    return [key for key in keys if not os.environ.get(key)]


def _require(keys: list[str]) -> None:
    absent = missing_env(keys)
    if absent:
        print("Missing environment variable: " + ", ".join(absent), file=sys.stderr)
        raise SystemExit(1)


def load_config(
    *,
    require_database: bool = True,
    require_spotify_app: bool = False,
    require_refresh: bool = False,
) -> Config:
    load_dotenv(ROOT / ".env")
    keys: list[str] = []
    if require_database:
        keys.append("DATABASE_URL")
    if require_spotify_app or require_refresh:
        keys.extend(["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REDIRECT_URI"])
    if require_refresh:
        keys.append("SPOTIFY_REFRESH_TOKEN")
    if keys:
        _require(keys)

    landing = Path(os.environ.get("LANDING_ROOT", "landing"))
    if not landing.is_absolute():
        landing = ROOT / landing

    return Config(
        database_url=os.environ.get("DATABASE_URL", ""),
        landing_root=landing,
        spotify_client_id=os.environ.get("SPOTIFY_CLIENT_ID", ""),
        spotify_client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET", ""),
        spotify_refresh_token=os.environ.get("SPOTIFY_REFRESH_TOKEN", ""),
        spotify_redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
        api_port=int(os.environ.get("API_PORT", "4000")),
        web_origin=os.environ.get("WEB_ORIGIN", "http://127.0.0.1:5173"),
        watchlist_path=ROOT / "seeds" / "watchlist.json",
    )
