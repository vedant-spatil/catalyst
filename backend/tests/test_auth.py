from pathlib import Path

from catalog_pipeline.config import missing_env
from catalog_pipeline.spotify_client import SpotifyClient


def test_auth3_missing_keys(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "")
    monkeypatch.setenv("SPOTIFY_REFRESH_TOKEN", "")
    missing = missing_env(["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN"])
    assert "SPOTIFY_CLIENT_ID" in missing
    assert "SPOTIFY_CLIENT_SECRET" in missing
    assert "SPOTIFY_REFRESH_TOKEN" in missing


def test_auth4_no_client_credentials_grant():
    source = Path("pipelines/catalog_pipeline/spotify_client.py").read_text(encoding="utf-8")
    assert "client_credentials" not in source
    client = SpotifyClient("id", "secret", "refresh")
    assert not hasattr(client, "client_credentials")
