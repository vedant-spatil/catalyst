import os

from fastapi.testclient import TestClient

from tests.conftest import requires_db


@requires_db
def test_routes_empty_then_match_mart():
    from catalog_api.main import app
    import psycopg
    from warehouse.apply_migrations import apply_migrations

    apply_migrations(os.environ["DATABASE_URL"])
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute("TRUNCATE gold.mart_playlist_exposure, gold.mart_release_curve, gold.mart_movers_losers, gold.mart_weekly_movement, ops.run_log CASCADE")
        conn.commit()

    client = TestClient(app)
    assert client.get("/exposure").json() == []
    assert client.get("/movers").json() == []
    assert client.get("/weekly").json() == []
    assert client.get("/release-curve").json() == []
    assert client.get("/runs/latest").json() is None

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute(
            """
            INSERT INTO gold.mart_playlist_exposure (
                snapshot_date, spotify_artist_id, artist_name, spotify_playlist_id,
                playlist_name, spotify_track_id, track_name, position
            ) VALUES ('2026-01-01', 'art1', 'Artist', 'pl1', 'P', 't1', 'Track', 1)
            """
        )
        conn.commit()
        try:
            rows = client.get("/exposure").json()
            assert rows[0]["track_name"] == "Track"
        finally:
            conn.execute("TRUNCATE gold.mart_playlist_exposure CASCADE")
            conn.commit()
