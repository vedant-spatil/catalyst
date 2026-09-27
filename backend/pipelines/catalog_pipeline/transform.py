from __future__ import annotations

from datetime import date, datetime

import psycopg
from psycopg.types.json import Json

from catalog_pipeline.config import load_config
from catalog_pipeline.extract import track_from_playlist_item


def _parse_release(value: str | None, precision: str | None) -> date | None:
    if not value:
        return None
    if precision == "day" and len(value) >= 10:
        return date.fromisoformat(value[:10])
    return None


def transform(snapshot_date: date | None = None) -> dict:
    cfg = load_config(require_database=True)
    with psycopg.connect(cfg.database_url) as conn:
        dates = [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT ingest_date FROM bronze.raw_payload ORDER BY ingest_date"
            )
        ]
        if snapshot_date:
            dates = [d for d in dates if d == snapshot_date]
        if not dates:
            return {"snapshots": 0}
        counts = {"artists": 0, "albums": 0, "tracks": 0, "facts": 0}
        for ingest_date in dates:
            with conn.transaction():
                _transform_date(conn, ingest_date, counts)
            conn.execute(
                """
                INSERT INTO ops.watermark (source, snapshot_date)
                VALUES ('spotify_playlists', %s)
                ON CONFLICT (source) DO UPDATE SET snapshot_date = EXCLUDED.snapshot_date, updated_at = now()
                """,
                (ingest_date,),
            )
        return {"snapshots": len(dates), **counts}


def _payloads(conn, ingest_date: date, entity: str) -> list:
    rows = conn.execute(
        """
        SELECT payload FROM bronze.raw_payload
        WHERE ingest_date = %s AND entity = %s
        ORDER BY loaded_at
        """,
        (ingest_date, entity),
    ).fetchall()
    items = []
    for (payload,) in rows:
        if isinstance(payload, list):
            items.extend(payload)
        else:
            items.append(payload)
    return items


def _ensure_date(conn, day: date) -> None:
    iso = day.isocalendar()
    conn.execute(
        """
        INSERT INTO gold.dim_date (date_key, iso_year, iso_week)
        VALUES (%s, %s, %s)
        ON CONFLICT (date_key) DO NOTHING
        """,
        (day, iso.year, iso.week),
    )


def _upsert_artist(conn, spotify_id: str, name: str, genres: list[str], image_url: str | None = None) -> int:
    conn.execute(
        """
        INSERT INTO silver.artist (spotify_artist_id, artist_name, genres, ingest_date)
        VALUES (%s, %s, %s, CURRENT_DATE)
        ON CONFLICT (spotify_artist_id) DO UPDATE
        SET artist_name = EXCLUDED.artist_name, genres = EXCLUDED.genres
        """,
        (spotify_id, name, genres),
    )
    conn.execute(
        """
        INSERT INTO gold.dim_artist (spotify_artist_id, artist_name, genres, image_url)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (spotify_artist_id) DO UPDATE
        SET artist_name = EXCLUDED.artist_name, genres = EXCLUDED.genres,
            image_url = COALESCE(EXCLUDED.image_url, gold.dim_artist.image_url)
        """,
        (spotify_id, name, genres, image_url),
    )
    return conn.execute(
        "SELECT artist_key FROM gold.dim_artist WHERE spotify_artist_id = %s",
        (spotify_id,),
    ).fetchone()[0]


def _upsert_album(conn, album: dict, artist_key: int | None) -> int | None:
    album_id = album.get("id")
    if not album_id:
        return None
    precision = album.get("release_date_precision")
    release = _parse_release(album.get("release_date"), precision)
    conn.execute(
        """
        INSERT INTO silver.album (
            spotify_album_id, album_name, release_date, release_date_precision,
            album_type, spotify_artist_id, ingest_date
        ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE)
        ON CONFLICT (spotify_album_id) DO UPDATE SET
            album_name = EXCLUDED.album_name,
            release_date = EXCLUDED.release_date,
            release_date_precision = EXCLUDED.release_date_precision,
            album_type = EXCLUDED.album_type
        """,
        (
            album_id,
            album.get("name") or "",
            album.get("release_date"),
            precision,
            album.get("album_type"),
            album.get("artist_id"),
        ),
    )
    conn.execute(
        """
        INSERT INTO gold.dim_album (
            spotify_album_id, album_name, album_type, release_date, release_date_precision, artist_key
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (spotify_album_id) DO UPDATE SET
            album_name = EXCLUDED.album_name,
            album_type = EXCLUDED.album_type,
            release_date = EXCLUDED.release_date,
            release_date_precision = EXCLUDED.release_date_precision,
            artist_key = COALESCE(EXCLUDED.artist_key, gold.dim_album.artist_key)
        """,
        (album_id, album.get("name") or "", album.get("album_type"), release, precision, artist_key),
    )
    return conn.execute(
        "SELECT album_key FROM gold.dim_album WHERE spotify_album_id = %s",
        (album_id,),
    ).fetchone()[0]


def _upsert_track(conn, track: dict, album_key: int | None, artist_key: int | None) -> int | None:
    track_id = track.get("id")
    if not track_id:
        conn.execute(
            """
            INSERT INTO silver.rejects (ingest_date, entity, reason, payload)
            VALUES (CURRENT_DATE, 'track', 'missing track id', %s)
            """,
            (Json(track),),
        )
        return None
    conn.execute(
        """
        INSERT INTO silver.track (
            spotify_track_id, track_name, duration_ms, disc_number, track_number,
            explicit, spotify_album_id, spotify_artist_id, ingest_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
        ON CONFLICT (spotify_track_id) DO UPDATE SET
            track_name = EXCLUDED.track_name,
            duration_ms = EXCLUDED.duration_ms,
            disc_number = EXCLUDED.disc_number,
            track_number = EXCLUDED.track_number,
            explicit = EXCLUDED.explicit
        """,
        (
            track_id,
            track.get("name") or "",
            track.get("duration_ms"),
            track.get("disc_number"),
            track.get("track_number"),
            track.get("explicit"),
            track.get("album_id"),
            track.get("artist_id"),
        ),
    )
    conn.execute(
        """
        INSERT INTO gold.dim_track (
            spotify_track_id, track_name, duration_ms, disc_number, track_number,
            explicit, album_key, artist_key
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (spotify_track_id) DO UPDATE SET
            track_name = EXCLUDED.track_name,
            duration_ms = EXCLUDED.duration_ms,
            disc_number = EXCLUDED.disc_number,
            track_number = EXCLUDED.track_number,
            explicit = EXCLUDED.explicit,
            album_key = COALESCE(EXCLUDED.album_key, gold.dim_track.album_key),
            artist_key = COALESCE(EXCLUDED.artist_key, gold.dim_track.artist_key)
        """,
        (
            track_id,
            track.get("name") or "",
            track.get("duration_ms"),
            track.get("disc_number"),
            track.get("track_number"),
            track.get("explicit"),
            album_key,
            artist_key,
        ),
    )
    return conn.execute(
        "SELECT track_key FROM gold.dim_track WHERE spotify_track_id = %s",
        (track_id,),
    ).fetchone()[0]


def _scd2_playlist(conn, playlist_id: str, name: str, ingest_date: date, collaborative: bool = False) -> int:
    conn.execute(
        """
        INSERT INTO silver.playlist (spotify_playlist_id, playlist_name, ingest_date, collaborative)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (spotify_playlist_id) DO UPDATE SET
            playlist_name = EXCLUDED.playlist_name,
            collaborative = EXCLUDED.collaborative
        """,
        (playlist_id, name, ingest_date, collaborative),
    )
    current = conn.execute(
        """
        SELECT playlist_key, playlist_name FROM gold.dim_playlist
        WHERE spotify_playlist_id = %s AND is_current
        """,
        (playlist_id,),
    ).fetchone()
    if current is None:
        conn.execute(
            """
            INSERT INTO gold.dim_playlist (
                spotify_playlist_id, playlist_name, valid_from, is_current, collaborative
            )
            VALUES (%s, %s, %s, TRUE, %s)
            """,
            (playlist_id, name, ingest_date, collaborative),
        )
    elif current[1] != name:
        conn.execute(
            """
            UPDATE gold.dim_playlist
            SET is_current = FALSE, valid_to = %s
            WHERE playlist_key = %s
            """,
            (ingest_date, current[0]),
        )
        conn.execute(
            """
            INSERT INTO gold.dim_playlist (
                spotify_playlist_id, playlist_name, valid_from, is_current, collaborative
            )
            VALUES (%s, %s, %s, TRUE, %s)
            """,
            (playlist_id, name, ingest_date, collaborative),
        )
    else:
        conn.execute(
            """
            UPDATE gold.dim_playlist SET collaborative = %s WHERE playlist_key = %s
            """,
            (collaborative, current[0]),
        )
    return conn.execute(
        """
        SELECT playlist_key FROM gold.dim_playlist
        WHERE spotify_playlist_id = %s AND is_current
        """,
        (playlist_id,),
    ).fetchone()[0]


def _rebuild_marts(conn) -> None:
    conn.execute("DELETE FROM gold.mart_playlist_exposure")
    conn.execute("DELETE FROM gold.mart_release_curve")
    conn.execute("DELETE FROM gold.mart_movers_losers")
    conn.execute("DELETE FROM gold.mart_weekly_movement")

    latest = conn.execute("SELECT MAX(snapshot_date) FROM gold.fact_playlist_membership").fetchone()[0]
    if latest is None:
        return

    conn.execute(
        """
        INSERT INTO gold.mart_playlist_exposure (
            snapshot_date, spotify_artist_id, artist_name, spotify_playlist_id,
            playlist_name, spotify_track_id, track_name, position, collaborative, artist_image_url
        )
        SELECT
            f.snapshot_date,
            a.spotify_artist_id,
            a.artist_name,
            p.spotify_playlist_id,
            p.playlist_name,
            t.spotify_track_id,
            t.track_name,
            f.position,
            COALESCE(p.collaborative, FALSE),
            a.image_url
        FROM gold.fact_playlist_membership f
        JOIN gold.dim_track t ON t.track_key = f.track_key
        JOIN gold.dim_playlist p ON p.playlist_key = f.playlist_key
        LEFT JOIN gold.dim_artist a ON a.artist_key = t.artist_key
        WHERE f.snapshot_date = %s
        """,
        (latest,),
    )

    conn.execute(
        """
        INSERT INTO gold.mart_release_curve (
            snapshot_date, spotify_track_id, track_name, days_since_release, playlist_count, best_position,
            artist_name, release_date
        )
        SELECT
            f.snapshot_date,
            t.spotify_track_id,
            t.track_name,
            CASE
                WHEN al.release_date IS NOT NULL AND al.release_date_precision = 'day'
                THEN (f.snapshot_date - al.release_date)
                ELSE NULL
            END,
            COUNT(*)::int,
            MIN(f.position),
            a.artist_name,
            CASE
                WHEN al.release_date_precision = 'day' THEN al.release_date
                ELSE NULL
            END
        FROM gold.fact_playlist_membership f
        JOIN gold.dim_track t ON t.track_key = f.track_key
        LEFT JOIN gold.dim_album al ON al.album_key = t.album_key
        LEFT JOIN gold.dim_artist a ON a.artist_key = t.artist_key
        GROUP BY 1, 2, 3, 4, 7, 8
        """
    )

    dates = [
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT snapshot_date FROM gold.fact_playlist_membership ORDER BY snapshot_date"
        )
    ]
    if len(dates) >= 2:
        prev, curr = dates[-2], dates[-1]
        conn.execute(
            """
            INSERT INTO gold.mart_movers_losers (
                from_snapshot, to_snapshot, spotify_track_id, track_name, artist_name, change, playlist_names
            )
            SELECT %s, %s, t.spotify_track_id, t.track_name, a.artist_name, 'added',
                   ARRAY_AGG(DISTINCT p.playlist_name ORDER BY p.playlist_name)
            FROM gold.fact_playlist_membership f
            JOIN gold.dim_track t ON t.track_key = f.track_key
            JOIN gold.dim_playlist p ON p.playlist_key = f.playlist_key
            LEFT JOIN gold.dim_artist a ON a.artist_key = t.artist_key
            WHERE f.snapshot_date = %s
              AND NOT EXISTS (
                  SELECT 1 FROM gold.fact_playlist_membership o
                  WHERE o.track_key = f.track_key
                    AND o.playlist_key = f.playlist_key
                    AND o.snapshot_date = %s
              )
            GROUP BY t.spotify_track_id, t.track_name, a.artist_name
            """,
            (prev, curr, curr, prev),
        )
        conn.execute(
            """
            INSERT INTO gold.mart_movers_losers (
                from_snapshot, to_snapshot, spotify_track_id, track_name, artist_name, change, playlist_names
            )
            SELECT %s, %s, t.spotify_track_id, t.track_name, a.artist_name, 'dropped',
                   ARRAY_AGG(DISTINCT p.playlist_name ORDER BY p.playlist_name)
            FROM gold.fact_playlist_membership f
            JOIN gold.dim_track t ON t.track_key = f.track_key
            JOIN gold.dim_playlist p ON p.playlist_key = f.playlist_key
            LEFT JOIN gold.dim_artist a ON a.artist_key = t.artist_key
            WHERE f.snapshot_date = %s
              AND NOT EXISTS (
                  SELECT 1 FROM gold.fact_playlist_membership o
                  WHERE o.track_key = f.track_key
                    AND o.playlist_key = f.playlist_key
                    AND o.snapshot_date = %s
              )
            GROUP BY t.spotify_track_id, t.track_name, a.artist_name
            """,
            (prev, curr, prev, curr),
        )

    week_dates = conn.execute(
        "SELECT COUNT(DISTINCT d.iso_year * 100 + d.iso_week) FROM gold.fact_playlist_membership f JOIN gold.dim_date d ON d.date_key = f.snapshot_date"
    ).fetchone()[0]
    if week_dates >= 2:
        conn.execute(
            """
            INSERT INTO gold.mart_weekly_movement (
                iso_year, iso_week, spotify_artist_id, artist_name, best_position, playlist_count
            )
            SELECT
                d.iso_year,
                d.iso_week,
                a.spotify_artist_id,
                a.artist_name,
                MIN(f.position),
                COUNT(DISTINCT f.playlist_key)::int
            FROM gold.fact_playlist_membership f
            JOIN gold.dim_date d ON d.date_key = f.snapshot_date
            JOIN gold.dim_track t ON t.track_key = f.track_key
            JOIN gold.dim_artist a ON a.artist_key = t.artist_key
            GROUP BY 1, 2, 3, 4
            """
        )


def _transform_date(conn, ingest_date: date, counts: dict) -> None:
    _ensure_date(conn, ingest_date)
    artist_keys: dict[str, int] = {}
    for artist in _payloads(conn, ingest_date, "artists"):
        if not artist.get("id"):
            continue
        artist_keys[artist["id"]] = _upsert_artist(
            conn,
            artist["id"],
            artist.get("name") or "",
            artist.get("genres") or [],
            artist.get("image_url"),
        )
        counts["artists"] += 1

    album_keys: dict[str, int] = {}
    for album in _payloads(conn, ingest_date, "albums"):
        artist_key = artist_keys.get(album.get("artist_id"))
        key = _upsert_album(conn, album, artist_key)
        if key:
            album_keys[album["id"]] = key
            counts["albums"] += 1

    track_keys: dict[str, int] = {}
    for track in _payloads(conn, ingest_date, "tracks"):
        album_key = album_keys.get(track.get("album_id"))
        artist_key = artist_keys.get(track.get("artist_id"))
        key = _upsert_track(conn, track, album_key, artist_key)
        if key:
            track_keys[track["id"]] = key
            counts["tracks"] += 1

    conn.execute(
        "DELETE FROM gold.fact_playlist_membership WHERE snapshot_date = %s",
        (ingest_date,),
    )
    conn.execute(
        "DELETE FROM silver.playlist_item WHERE ingest_date = %s",
        (ingest_date,),
    )

    for playlist in _payloads(conn, ingest_date, "playlist_items"):
        playlist_id = playlist.get("id")
        if not playlist_id:
            continue
        playlist_key = _scd2_playlist(
            conn,
            playlist_id,
            playlist.get("name") or "",
            ingest_date,
            bool(playlist.get("collaborative")),
        )
        for item in playlist.get("items") or []:
            track_id = item.get("track_id")
            added_at = item.get("added_at")
            nested = None
            if item.get("reject") or not track_id:
                nested = track_from_playlist_item(item.get("raw") or {})
                if not nested:
                    conn.execute(
                        """
                        INSERT INTO silver.rejects (ingest_date, entity, reason, payload)
                        VALUES (%s, 'playlist_item', 'missing track id', %s)
                        """,
                        (ingest_date, Json(item)),
                    )
                    continue
                track_id = nested["id"]
                added_at = (item.get("raw") or {}).get("added_at") or added_at
            position = item.get("position")
            if not isinstance(position, int) or position < 1:
                conn.execute(
                    """
                    INSERT INTO silver.rejects (ingest_date, entity, reason, payload)
                    VALUES (%s, 'playlist_item', 'bad position', %s)
                    """,
                    (ingest_date, Json(item)),
                )
                continue
            if nested:
                album = nested.get("album") or {}
                artists_on_track = nested.get("artists") or []
                first = artists_on_track[0] if artists_on_track else {}
                artist_id = first.get("id")
                artist_key = artist_keys.get(artist_id) if artist_id else None
                if artist_id and artist_key is None:
                    artist_key = _upsert_artist(conn, artist_id, first.get("name") or "", [], None)
                    artist_keys[artist_id] = artist_key
                album_key = album_keys.get(album.get("id")) if album.get("id") else None
                if album.get("id") and album_key is None:
                    album_key = _upsert_album(
                        conn,
                        {
                            "id": album.get("id"),
                            "name": album.get("name"),
                            "release_date": album.get("release_date"),
                            "release_date_precision": album.get("release_date_precision"),
                            "album_type": album.get("album_type") or album.get("type"),
                            "artist_id": artist_id,
                        },
                        artist_key,
                    )
                    if album_key:
                        album_keys[album["id"]] = album_key
                track_key = _upsert_track(
                    conn,
                    {
                        "id": nested.get("id"),
                        "name": nested.get("name"),
                        "duration_ms": nested.get("duration_ms"),
                        "disc_number": nested.get("disc_number"),
                        "track_number": nested.get("track_number"),
                        "explicit": nested.get("explicit"),
                        "album_id": album.get("id"),
                        "artist_id": artist_id,
                    },
                    album_key,
                    artist_key,
                )
                if track_key:
                    track_keys[track_id] = track_key
            track_key = track_keys.get(track_id)
            if track_key is None:
                row = conn.execute(
                    "SELECT track_key FROM gold.dim_track WHERE spotify_track_id = %s",
                    (track_id,),
                ).fetchone()
                track_key = row[0] if row else None
            if track_key is None:
                conn.execute(
                    """
                    INSERT INTO silver.rejects (ingest_date, entity, reason, payload)
                    VALUES (%s, 'playlist_item', 'unknown track', %s)
                    """,
                    (ingest_date, Json(item)),
                )
                continue
            parsed_added = None
            if added_at:
                parsed_added = datetime.fromisoformat(str(added_at).replace("Z", "+00:00"))
            conn.execute(
                """
                INSERT INTO silver.playlist_item (
                    ingest_date, spotify_playlist_id, spotify_track_id, position, added_at
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (ingest_date, playlist_id, track_id, position, parsed_added),
            )
            conn.execute(
                """
                INSERT INTO gold.fact_playlist_membership (
                    playlist_key, track_key, snapshot_date, position, added_at
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (playlist_key, track_key, snapshot_date) DO UPDATE
                SET position = EXCLUDED.position, added_at = EXCLUDED.added_at
                """,
                (playlist_key, track_key, ingest_date, position, parsed_added),
            )
            counts["facts"] += 1

    _rebuild_marts(conn)
