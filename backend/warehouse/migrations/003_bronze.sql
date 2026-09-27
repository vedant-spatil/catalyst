CREATE TABLE IF NOT EXISTS bronze.raw_payload (
    file_hash TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    entity TEXT NOT NULL,
    ingest_date DATE NOT NULL,
    payload JSONB NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
