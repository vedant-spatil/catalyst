from pathlib import Path

from catalog_pipeline.extract import extract, track_from_playlist_item


def test_extract_refuses_empty_watchlist(tmp_path, monkeypatch):
    watch = tmp_path / "watchlist.json"
    watch.write_text('{"artist_ids": [], "playlist_ids": []}', encoding="utf-8")
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "x")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "y")
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    monkeypatch.setenv("SPOTIFY_REFRESH_TOKEN", "z")
    monkeypatch.setattr("catalog_pipeline.extract.load_config", lambda **kwargs: type(
        "C",
        (),
        {
            "watchlist_path": watch,
            "landing_root": tmp_path,
            "spotify_client_id": "x",
            "spotify_client_secret": "y",
            "spotify_refresh_token": "z",
        },
    )())
    try:
        extract()
        raise AssertionError("should exit")
    except SystemExit as exc:
        assert "watchlist" in str(exc)


def test_playlist_item_uses_item_when_track_is_bool():
    raw = {
        "added_at": "2026-03-01T10:32:18Z",
        "track": True,
        "item": {"id": "abc", "name": "Song", "type": "track"},
    }
    got = track_from_playlist_item(raw)
    assert got["id"] == "abc"


def test_extract_module_does_not_call_search():
    text = Path("pipelines/catalog_pipeline/extract.py").read_text(encoding="utf-8")
    assert ".search(" not in text
    assert "/search" not in text
