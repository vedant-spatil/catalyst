# Catalyst frontend

The dashboard for a small artist roster’s playlist membership. It reads snapshot marts from the Catalyst API and shows four views:

- **Exposure** lists roster tracks on the watched playlists in the latest snapshot, with playlist slot. Search waits 300ms before filtering.
- **Release curve** charts playlist count and best slot for one track across snapshots.
- **Movers** lists tracks added or dropped between the two latest snapshot dates.
- **Weekly** charts playlist count and best slot by ISO week.

Slot 1 is the top of the playlist. The header shows the latest pipeline run.

## Setup

The API should already be up at `http://127.0.0.1:4000` (`docker compose up` in `backend/`).

```bash
pnpm install
pnpm dev
```

Open **http://127.0.0.1:5173**.

Point at another API with `VITE_API_URL`:

```bash
VITE_API_URL=http://127.0.0.1:4000 pnpm dev
```

Production image, same variable at build time:

```bash
docker build --build-arg VITE_API_URL=http://127.0.0.1:4000 -t catalyst-web .
```

## Tests

```bash
pnpm test
```
