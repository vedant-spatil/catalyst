# Catalyst

Catalyst is a playlist catalog for a small artist roster. It snapshots playlists you own or collaborate on, then shows where each track sits and how that membership changes over time.

An artist manager picks the artists and the playlists they actually work with. Each pipeline run stores that day’s membership: which tracks are on which playlists, and in which slot. The dashboard reads those snapshots.

Four screens:

- **Exposure** shows every roster track on the watched playlists in the latest snapshot, including playlist slot.
- **Release curve** follows playlist count and best slot for a track across snapshots after its release date.
- **Movers** lists tracks added or dropped between the two latest snapshot dates.
- **Weekly** rolls playlist count and best slot up by ISO week.

Playlist slot is the position on that playlist. Slot 1 is the top.

## Layout

| Folder | What it is |
| --- | --- |
| `backend/` | Postgres warehouse, Spotify pipeline, FastAPI |
| `frontend/` | React dashboard |
| `markdowns/` | Design notes |

`backend/` and `frontend/` are separate git repositories. Run commands inside the folder they belong to.

## Setup

You need Docker, Python 3.12, pnpm, and a Spotify app in Development Mode. In the Spotify dashboard set the redirect URI to `http://127.0.0.1:8888/callback`.

### 1. Backend environment

```bash
cd backend
cp .env.example .env
```

Fill `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`. Leave the refresh token empty until login. `.env` stays local.

### 2. Warehouse and API

```bash
cd backend
docker compose up -d --build
docker compose logs seed
```

Compose starts Postgres 16 on host port **5433**, loads landing files, builds the warehouse, and serves the API on **http://127.0.0.1:4000**.

### 3. Spotify login and watchlist

On the host, with Postgres already up:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m catalog_pipeline login
```

The browser login writes `SPOTIFY_REFRESH_TOKEN` into `.env`. Scopes are `playlist-read-private` and `playlist-read-collaborative`.

List your playlists and search the catalog, then put the ids you want into `seeds/watchlist.json`:

```bash
python -m catalog_pipeline playlists
python -m catalog_pipeline search --q "artist name"
```

`artist_ids` are Spotify artist ids. `playlist_ids` are playlists this Spotify user owns or collaborates on. Both arrays need at least one id.

Pull a snapshot into the warehouse:

```bash
python -m catalog_pipeline run
```

Run it again on a later day to add another snapshot. Movers and weekly trends use two snapshot dates or two ISO weeks.

### 4. Dashboard

```bash
cd frontend
pnpm install
pnpm dev
```

Open **http://127.0.0.1:5173**. The UI calls the API at `http://127.0.0.1:4000`. Set `VITE_API_URL` if the API lives somewhere else.

## Tests

From `backend/`, `pytest` covers the pipeline with a fake Spotify HTTP layer. Postgres-backed cases run when `DATABASE_URL` is up. From `frontend/`, `pnpm test` runs the UI tests.
