"""Apply numbered warehouse SQL files in order. Records ops.schema_migrations."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Missing environment variable: DATABASE_URL", file=sys.stderr)
        raise SystemExit(1)
    return url


def _statements(sql: str) -> list[str]:
    return [part.strip() for part in sql.split(";") if part.strip()]


def apply_migrations(database_url: str | None = None) -> list[str]:
    url = database_url or _database_url()
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        raise SystemExit(f"No migration files in {MIGRATIONS_DIR}")
    versions = [path.stem for path in files]
    if versions != sorted(versions):
        raise SystemExit("Migration filenames are not in lexical order")

    applied: list[str] = []
    with psycopg.connect(url) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS ops")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ops.schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.commit()
        done = {row[0] for row in conn.execute("SELECT version FROM ops.schema_migrations")}
        for path in files:
            version = path.stem
            if version in done:
                continue
            sql = path.read_text(encoding="utf-8")
            with conn.transaction():
                for statement in _statements(sql):
                    conn.execute(statement)
                conn.execute(
                    "INSERT INTO ops.schema_migrations (version) VALUES (%s)",
                    (version,),
                )
            applied.append(version)
            done.add(version)
    return applied


def main() -> None:
    applied = apply_migrations()
    if applied:
        print("Applied: " + ", ".join(applied))
    else:
        print("No pending migrations")


if __name__ == "__main__":
    main()
