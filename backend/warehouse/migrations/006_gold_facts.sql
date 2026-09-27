CREATE TABLE IF NOT EXISTS gold.fact_playlist_membership (
    playlist_key BIGINT NOT NULL REFERENCES gold.dim_playlist (playlist_key),
    track_key BIGINT NOT NULL REFERENCES gold.dim_track (track_key),
    snapshot_date DATE NOT NULL REFERENCES gold.dim_date (date_key),
    position INTEGER NOT NULL CHECK (position >= 1),
    added_at TIMESTAMPTZ,
    PRIMARY KEY (playlist_key, track_key, snapshot_date)
);
