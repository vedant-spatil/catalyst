CREATE TABLE IF NOT EXISTS silver.artist (
    spotify_artist_id TEXT PRIMARY KEY,
    artist_name TEXT NOT NULL,
    genres TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    ingest_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS silver.album (
    spotify_album_id TEXT PRIMARY KEY,
    album_name TEXT NOT NULL,
    release_date TEXT,
    release_date_precision TEXT,
    album_type TEXT,
    spotify_artist_id TEXT,
    ingest_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS silver.track (
    spotify_track_id TEXT PRIMARY KEY,
    track_name TEXT NOT NULL,
    duration_ms INTEGER,
    disc_number INTEGER,
    track_number INTEGER,
    explicit BOOLEAN,
    spotify_album_id TEXT,
    spotify_artist_id TEXT,
    ingest_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS silver.playlist (
    spotify_playlist_id TEXT PRIMARY KEY,
    playlist_name TEXT NOT NULL,
    ingest_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS silver.playlist_item (
    ingest_date DATE NOT NULL,
    spotify_playlist_id TEXT NOT NULL,
    spotify_track_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    added_at TIMESTAMPTZ,
    PRIMARY KEY (ingest_date, spotify_playlist_id, spotify_track_id)
);

CREATE TABLE IF NOT EXISTS silver.rejects (
    reject_id BIGSERIAL PRIMARY KEY,
    ingest_date DATE,
    entity TEXT NOT NULL,
    reason TEXT NOT NULL,
    payload JSONB NOT NULL,
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
