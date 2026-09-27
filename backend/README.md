# Catalyst backend

The backend keeps a Postgres warehouse of playlist membership for a small artist roster. Each run snapshots playlists the Spotify user owns or collaborates on: track, playlist, slot, and date. FastAPI serves that warehouse to the Catalyst dashboard.

The API is read-only:

| Route | What it returns |
| --- | --- |
| `GET /exposure` | Roster tracks on watched playlists in the latest snapshot |
| `GET /release-curve` | Playlist count and best slot for a track across snapshots |
| `GET /movers` | Tracks added or dropped between the two latest snapshot dates |
| `GET /weekly` | Playlist count and best slot by ISO week |
| `GET /runs/latest` | The latest pipeline run |

Slot 1 is the top of the playlist. Movers need two snapshot dates. Weekly trends need two ISO weeks.

## Setup

Copy the env file and fill the Spotify app credentials:

```bash
cp .env.example .env
```

`DATABASE_URL` points at Postgres on the host at `127.0.0.1:5433`. Inside Compose, the API and seed use the `postgres` service on port 5432. Keep `.env` out of git.

Start the warehouse and API:

```bash
docker compose up -d --build
docker compose logs seed
```

That brings up Postgres 16, applies SQL migrations in `warehouse/migrations/`, loads JSON from `landing/`, and serves the API on port **4000**.

To pull a new snapshot from Spotify, use a host virtualenv against the same database:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m catalog_pipeline login
python -m catalog_pipeline playlists
python -m catalog_pipeline search --q "artist name"
```

Login opens `http://127.0.0.1:8888/callback` and writes `SPOTIFY_REFRESH_TOKEN` into `.env`. Put artist ids and owned or collaborative playlist ids in `seeds/watchlist.json`, then:

```bash
python -m catalog_pipeline run
```

`run` extracts the watchlist, writes landing files, loads them, and rebuilds the marts. `login`, `playlists`, `search`, `extract`, `load`, `transform`, and `migrate` are the same steps on their own.

## Tests

```bash
pytest
```

Spotify calls use a fake HTTP layer. Cases that need Postgres run when `DATABASE_URL` is reachable. Set `SPOTIFY_LIVE_TESTS=1` to hit Spotify from tests.
