ALTER TABLE gold.dim_artist ADD COLUMN IF NOT EXISTS image_url TEXT;
ALTER TABLE gold.dim_playlist ADD COLUMN IF NOT EXISTS collaborative BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE silver.playlist ADD COLUMN IF NOT EXISTS collaborative BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE gold.mart_playlist_exposure ADD COLUMN IF NOT EXISTS collaborative BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE gold.mart_playlist_exposure ADD COLUMN IF NOT EXISTS artist_image_url TEXT;

ALTER TABLE gold.mart_release_curve ADD COLUMN IF NOT EXISTS artist_name TEXT;
ALTER TABLE gold.mart_release_curve ADD COLUMN IF NOT EXISTS release_date DATE;

ALTER TABLE gold.mart_movers_losers ADD COLUMN IF NOT EXISTS artist_name TEXT;
ALTER TABLE gold.mart_movers_losers ADD COLUMN IF NOT EXISTS playlist_names TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];
