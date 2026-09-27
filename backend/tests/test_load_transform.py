from datetime import date
import json

import psycopg

from catalog_pipeline.transform import transform
from tests.conftest import requires_db
from warehouse.apply_migrations import apply_migrations


def _seed_snapshot(conn, day: date, playlist_name: str, track_id: str, track_name: str) -> None:
    conn.execute(
        """
        INSERT INTO bronze.raw_payload (file_hash, path, entity, ingest_date, payload)
        VALUES (%s, %s, 'artists', %s, %s::jsonb)
        ON CONFLICT (file_hash) DO NOTHING
        """,
        (
            f"a-{day}-{track_id}",
            f"artists-{day}",
            day,
            '[{"id": "art1", "name": "Artist One", "genres": []}]',
        ),
    )
    conn.execute(
        """
        INSERT INTO bronze.raw_payload (file_hash, path, entity, ingest_date, payload)
        VALUES (%s, %s, 'albums', %s, %s::jsonb)
        ON CONFLICT (file_hash) DO NOTHING
        """,
        (
            f"al-{day}-{track_id}",
            f"albums-{day}",
            day,
            '[{"id": "alb1", "name": "Album", "release_date": "2024-01-15", "release_date_precision": "day", "album_type": "album", "artist_id": "art1"}]',
        ),
    )
    conn.execute(
        """
        INSERT INTO bronze.raw_payload (file_hash, path, entity, ingest_date, payload)
        VALUES (%s, %s, 'tracks', %s, %s::jsonb)
        ON CONFLICT (file_hash) DO NOTHING
        """,
        (
            f"t-{day}-{track_id}",
            f"tracks-{day}",
            day,
            f'[{{"id": "{track_id}", "name": "{track_name}", "duration_ms": 1000, "disc_number": 1, "track_number": 1, "explicit": false, "album_id": "alb1", "artist_id": "art1"}}]',
        ),
    )
    conn.execute(
        """
        INSERT INTO bronze.raw_payload (file_hash, path, entity, ingest_date, payload)
        VALUES (%s, %s, 'playlist_items', %s, %s::jsonb)
        ON CONFLICT (file_hash) DO NOTHING
        """,
        (
            f"p-{day}-{track_id}",
            f"playlists-{day}",
            day,
            json.dumps(
                [
                    {
                        "id": "pl1",
                        "name": playlist_name,
                        "items": [{"track_id": track_id, "position": 1, "added_at": "2024-01-01T00:00:00Z"}],
                    }
                ]
            ),
        ),
    )


@requires_db
def test_migrations_and_single_snapshot_empty_movers(monkeypatch):
    import os

    url = os.environ["DATABASE_URL"]
    apply_migrations(url)
    with psycopg.connect(url) as conn:
        conn.execute("TRUNCATE gold.fact_playlist_membership, gold.mart_playlist_exposure, gold.mart_release_curve, gold.mart_movers_losers, gold.mart_weekly_movement, gold.dim_playlist, gold.dim_track, gold.dim_album, gold.dim_artist, gold.dim_date, silver.rejects, silver.playlist_item, silver.playlist, silver.track, silver.album, silver.artist, bronze.raw_payload, ops.file_registry, ops.watermark, ops.run_log CASCADE")
        _seed_snapshot(conn, date(2026, 1, 1), "Roster A", "trk1", "Track One")
        conn.commit()
    transform(date(2026, 1, 1))
    with psycopg.connect(url) as conn:
        exposure = conn.execute("SELECT COUNT(*) FROM gold.mart_playlist_exposure").fetchone()[0]
        movers = conn.execute("SELECT COUNT(*) FROM gold.mart_movers_losers").fetchone()[0]
        current = conn.execute("SELECT COUNT(*) FROM gold.dim_playlist WHERE is_current").fetchone()[0]
        facts = conn.execute("SELECT COUNT(*) FROM gold.fact_playlist_membership").fetchone()[0]
        assert exposure == facts
        assert movers == 0
        assert current == 1


@requires_db
def test_scd2_playlist_name_and_second_snapshot_movers():
    import os

    url = os.environ["DATABASE_URL"]
    apply_migrations(url)
    with psycopg.connect(url) as conn:
        conn.execute("TRUNCATE gold.fact_playlist_membership, gold.mart_playlist_exposure, gold.mart_release_curve, gold.mart_movers_losers, gold.mart_weekly_movement, gold.dim_playlist, gold.dim_track, gold.dim_album, gold.dim_artist, gold.dim_date, silver.rejects, silver.playlist_item, silver.playlist, silver.track, silver.album, silver.artist, bronze.raw_payload, ops.file_registry, ops.watermark, ops.run_log CASCADE")
        _seed_snapshot(conn, date(2026, 1, 1), "Roster A", "trk1", "Track One")
        _seed_snapshot(conn, date(2026, 1, 8), "Roster B", "trk2", "Track Two")
        conn.commit()
    transform(date(2026, 1, 1))
    transform(date(2026, 1, 8))
    with psycopg.connect(url) as conn:
        names = [row[0] for row in conn.execute("SELECT playlist_name FROM gold.dim_playlist ORDER BY playlist_key")]
        current = conn.execute("SELECT playlist_name FROM gold.dim_playlist WHERE is_current").fetchone()[0]
        movers = conn.execute("SELECT change FROM gold.mart_movers_losers ORDER BY change").fetchall()
        assert "Roster A" in names
        assert current == "Roster B"
        assert ("added",) in movers
        assert ("dropped",) in movers
