from __future__ import annotations

import json
from datetime import date, datetime, timezone

from catalog_pipeline.config import load_config
from catalog_pipeline.landing import write_batch
from catalog_pipeline.spotify_client import SpotifyClient, SpotifyError


def track_from_playlist_item(raw: dict) -> dict | None:
    # Spotify may send track as a bool; the object lives under item.
    obj = raw.get("track")
    if not isinstance(obj, dict):
        obj = raw.get("item")
    if not isinstance(obj, dict):
        return None
    if not obj.get("id"):
        return None
    if obj.get("type") == "episode":
        return None
    return obj


def _today() -> str:
    return date.today().isoformat()


def _load_watchlist(path) -> tuple[list[str], list[str]]:
    if not path.exists():
        raise SystemExit("Missing seeds/watchlist.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    artists = [a for a in data.get("artist_ids") or [] if a]
    playlists = [p for p in data.get("playlist_ids") or [] if p]
    if not artists or not playlists:
        raise SystemExit("seeds/watchlist.json must list real artist_ids and playlist_ids")
    return artists, playlists


def extract() -> dict:
    cfg = load_config(require_database=False, require_spotify_app=True, require_refresh=True)
    artist_ids, playlist_ids = _load_watchlist(cfg.watchlist_path)
    ingest_date = _today()
    errors: list[dict] = []
    client = SpotifyClient(cfg.spotify_client_id, cfg.spotify_client_secret, cfg.spotify_refresh_token)
    artists: list[dict] = []
    albums: list[dict] = []
    tracks: list[dict] = []
    playlist_docs: list[dict] = []
    seen_track_ids: set[str] = set()
    seen_album_ids: set[str] = set()

    try:
        for artist_id in artist_ids:
            try:
                artist = client.get_artist(artist_id)
                artists.append(
                    {
                        "id": artist.get("id"),
                        "name": artist.get("name"),
                        "genres": artist.get("genres") or [],
                        "image_url": ((artist.get("images") or [{}])[0] or {}).get("url"),
                    }
                )
                album_list = client.get_artist_albums(artist_id)
            except SpotifyError as exc:
                errors.append({"entity": "artist", "id": artist_id, "status": exc.status, "path": exc.path})
                continue
            for summary in album_list:
                album_id = summary.get("id")
                if not album_id or album_id in seen_album_ids:
                    continue
                seen_album_ids.add(album_id)
                try:
                    album = client.get_album(album_id)
                except SpotifyError as exc:
                    errors.append({"entity": "album", "id": album_id, "status": exc.status, "path": exc.path})
                    continue
                albums.append(
                    {
                        "id": album.get("id"),
                        "name": album.get("name"),
                        "release_date": album.get("release_date"),
                        "release_date_precision": album.get("release_date_precision"),
                        "album_type": album.get("album_type"),
                        "artist_id": artist_id,
                    }
                )
                try:
                    album_tracks = client.get_album_tracks(album_id)
                except SpotifyError as exc:
                    errors.append({"entity": "album_tracks", "id": album_id, "status": exc.status, "path": exc.path})
                    continue
                for item in album_tracks:
                    track_id = item.get("id")
                    if not track_id:
                        continue
                    seen_track_ids.add(track_id)
                    tracks.append(
                        {
                            "id": track_id,
                            "name": item.get("name"),
                            "duration_ms": item.get("duration_ms"),
                            "disc_number": item.get("disc_number"),
                            "track_number": item.get("track_number"),
                            "explicit": item.get("explicit"),
                            "album_id": album_id,
                            "artist_id": artist_id,
                        }
                    )

        try:
            client.get_me_playlists()
        except SpotifyError as exc:
            if exc.status == 403:
                raise SystemExit("GET /me/playlists returned 403") from exc
            errors.append({"entity": "me_playlists", "status": exc.status, "path": exc.path})

        for playlist_id in playlist_ids:
            try:
                playlist = client.get_playlist(playlist_id)
            except SpotifyError as exc:
                errors.append({"entity": "playlist", "id": playlist_id, "status": exc.status, "path": exc.path})
                continue
            items: list[dict] = []
            try:
                raw_items = client.get_playlist_items(playlist_id)
            except SpotifyError as exc:
                errors.append({"entity": "playlist_items", "id": playlist_id, "status": exc.status, "path": exc.path})
                raw_items = []
            position = 0
            for raw in raw_items:
                position += 1
                track = track_from_playlist_item(raw)
                if not track:
                    items.append({"reject": True, "position": position, "raw": raw})
                    continue
                track_id = track["id"]
                items.append(
                    {
                        "track_id": track_id,
                        "position": position,
                        "added_at": raw.get("added_at"),
                    }
                )
                if track_id in seen_track_ids:
                    continue
                album = track.get("album") or {}
                artists_on_track = track.get("artists") or []
                tracks.append(
                    {
                        "id": track.get("id"),
                        "name": track.get("name"),
                        "duration_ms": track.get("duration_ms"),
                        "disc_number": track.get("disc_number"),
                        "track_number": track.get("track_number"),
                        "explicit": track.get("explicit"),
                        "album_id": album.get("id"),
                        "artist_id": (artists_on_track[0] or {}).get("id") if artists_on_track else None,
                    }
                )
                seen_track_ids.add(track_id)
            playlist_docs.append(
                {
                    "id": playlist.get("id"),
                    "name": playlist.get("name"),
                    "collaborative": bool(playlist.get("collaborative")),
                    "items": items,
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                }
            )
    finally:
        client.close()

    write_batch(cfg.landing_root, ingest_date, "artists", artists)
    write_batch(cfg.landing_root, ingest_date, "albums", albums)
    write_batch(cfg.landing_root, ingest_date, "tracks", tracks)
    write_batch(cfg.landing_root, ingest_date, "playlist_items", playlist_docs)
    return {"ingest_date": ingest_date, "errors": errors}
