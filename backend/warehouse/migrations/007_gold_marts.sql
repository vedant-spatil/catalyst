CREATE TABLE IF NOT EXISTS gold.mart_playlist_exposure (
    snapshot_date DATE NOT NULL,
    spotify_artist_id TEXT,
    artist_name TEXT,
    spotify_playlist_id TEXT NOT NULL,
    playlist_name TEXT NOT NULL,
    spotify_track_id TEXT NOT NULL,
    track_name TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (snapshot_date, spotify_playlist_id, spotify_track_id)
);

CREATE TABLE IF NOT EXISTS gold.mart_release_curve (
    snapshot_date DATE NOT NULL,
    spotify_track_id TEXT NOT NULL,
    track_name TEXT NOT NULL,
    days_since_release INTEGER,
    playlist_count INTEGER NOT NULL,
    best_position INTEGER,
    PRIMARY KEY (snapshot_date, spotify_track_id)
);

CREATE TABLE IF NOT EXISTS gold.mart_movers_losers (
    from_snapshot DATE NOT NULL,
    to_snapshot DATE NOT NULL,
    spotify_track_id TEXT NOT NULL,
    track_name TEXT NOT NULL,
    change TEXT NOT NULL,
    PRIMARY KEY (from_snapshot, to_snapshot, spotify_track_id, change)
);

CREATE TABLE IF NOT EXISTS gold.mart_weekly_movement (
    iso_year INTEGER NOT NULL,
    iso_week INTEGER NOT NULL,
    spotify_artist_id TEXT NOT NULL,
    artist_name TEXT NOT NULL,
    best_position INTEGER,
    playlist_count INTEGER NOT NULL,
    PRIMARY KEY (iso_year, iso_week, spotify_artist_id)
);
