CREATE TABLE IF NOT EXISTS ops.schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ops.run_log (
    run_id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    command TEXT NOT NULL,
    snapshot_date DATE,
    row_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_list JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS ops.watermark (
    source TEXT PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ops.file_registry (
    file_hash TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    entity TEXT NOT NULL,
    ingest_date DATE NOT NULL,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
