CREATE TABLE IF NOT EXISTS gold.dim_date (
    date_key DATE PRIMARY KEY,
    iso_year INTEGER NOT NULL,
    iso_week INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.dim_artist (
    artist_key BIGSERIAL PRIMARY KEY,
    spotify_artist_id TEXT NOT NULL UNIQUE,
    artist_name TEXT NOT NULL,
    genres TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[]
);

CREATE TABLE IF NOT EXISTS gold.dim_album (
    album_key BIGSERIAL PRIMARY KEY,
    spotify_album_id TEXT NOT NULL UNIQUE,
    album_name TEXT NOT NULL,
    album_type TEXT,
    release_date DATE,
    release_date_precision TEXT,
    artist_key BIGINT REFERENCES gold.dim_artist (artist_key)
);

CREATE TABLE IF NOT EXISTS gold.dim_track (
    track_key BIGSERIAL PRIMARY KEY,
    spotify_track_id TEXT NOT NULL UNIQUE,
    track_name TEXT NOT NULL,
    duration_ms INTEGER,
    disc_number INTEGER,
    track_number INTEGER,
    explicit BOOLEAN,
    album_key BIGINT REFERENCES gold.dim_album (album_key),
    artist_key BIGINT REFERENCES gold.dim_artist (artist_key)
);

CREATE TABLE IF NOT EXISTS gold.dim_playlist (
    playlist_key BIGSERIAL PRIMARY KEY,
    spotify_playlist_id TEXT NOT NULL,
    playlist_name TEXT NOT NULL,
    valid_from DATE NOT NULL,
    valid_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE UNIQUE INDEX IF NOT EXISTS dim_playlist_one_current
    ON gold.dim_playlist (spotify_playlist_id)
    WHERE is_current;

CREATE INDEX IF NOT EXISTS dim_playlist_nk
    ON gold.dim_playlist (spotify_playlist_id);
