import { useEffect, useMemo, useState } from "react";
import Avatar from "../Avatar";
import BarChart from "../BarChart";
import { getJson } from "../api";
import { formatDate } from "../format";
import type { ExposureRow } from "../types";
import PageIntro from "../PageIntro";
import EmptyState from "./EmptyState";

export default function Exposure() {
  const [rows, setRows] = useState<ExposureRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [artistFilter, setArtistFilter] = useState("all");
  const [open, setOpen] = useState<Record<string, boolean>>({});

  useEffect(() => {
    getJson<ExposureRow[]>("/exposure")
      .then(setRows)
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    const handle = window.setTimeout(() => setDebouncedQuery(query), 300);
    return () => window.clearTimeout(handle);
  }, [query]);

  const artists = useMemo(() => {
    if (!rows) return [];
    const names = new Set<string>();
    for (const row of rows) {
      names.add(row.artist_name || "Unknown artist");
    }
    return [...names].sort();
  }, [rows]);

  const filtered = useMemo(() => {
    if (!rows) return [];
    const q = debouncedQuery.trim().toLowerCase();
    return rows.filter((row) => {
      const artist = row.artist_name || "Unknown artist";
      if (artistFilter !== "all" && artist !== artistFilter) return false;
      if (!q) return true;
      const blob = `${artist} ${row.playlist_name} ${row.track_name}`.toLowerCase();
      return blob.includes(q);
    });
  }, [rows, debouncedQuery, artistFilter]);

  const groups = useMemo(() => {
    const map = new Map<
      string,
      { name: string; image: string | null; rows: ExposureRow[]; best: number }
    >();
    for (const row of filtered) {
      const key = row.spotify_artist_id || row.artist_name || "unknown";
      const name = row.artist_name || "Unknown artist";
      let g = map.get(key);
      if (!g) {
        g = { name, image: row.artist_image_url, rows: [], best: row.position };
        map.set(key, g);
      }
      g.rows.push(row);
      if (row.position < g.best) g.best = row.position;
    }
    for (const g of map.values()) {
      g.rows.sort((a, b) => a.position - b.position);
    }
    return [...map.values()].sort((a, b) => a.name.localeCompare(b.name));
  }, [filtered]);

  if (error) return <p className="banner error">{error}</p>;
  if (!rows) return <p className="banner">Loading...</p>;
  if (rows.length === 0) {
    return (
      <EmptyState
        title="No playlist exposure yet"
        description="Run the catalog pipeline to create the first committed snapshot."
      />
    );
  }

  const artistCount = new Set(rows.map((r) => r.spotify_artist_id || r.artist_name)).size;
  const owned = new Set(rows.filter((r) => !r.collaborative).map((r) => r.spotify_playlist_id)).size;
  const collab = new Set(rows.filter((r) => r.collaborative).map((r) => r.spotify_playlist_id)).size;
  const snapshot = rows[0].snapshot_date;
  const byPlaylist = new Map<string, { name: string; count: number; best: number }>();
  for (const row of rows) {
    const hit = byPlaylist.get(row.spotify_playlist_id);
    if (!hit) {
      byPlaylist.set(row.spotify_playlist_id, { name: row.playlist_name, count: 1, best: row.position });
    } else {
      hit.count += 1;
      if (row.position < hit.best) hit.best = row.position;
    }
  }
  const playlistBars = [...byPlaylist.values()].sort((a, b) => b.count - a.count || a.best - b.best).slice(0, 12);

  return (
    <>
      <PageIntro
        eyebrow="PLAYLIST EXPOSURE"
        title="Playlist Exposure"
        description="All playlists currently including our roster artists from the latest snapshot."
        extra={
          <label className="control">
            Snapshot date
            <input readOnly value={formatDate(snapshot)} />
          </label>
        }
      />
      <div className="kpis">
        <article className="kpi">
          <strong>{artistCount}</strong>
          <span>Roster artists</span>
          <small>with playlist placements</small>
        </article>
        <article className="kpi">
          <strong>{rows.length}</strong>
          <span>Total playlist placements</span>
          <small>across all artists</small>
        </article>
        <article className="kpi">
          <strong>{owned}</strong>
          <span>Owned playlists</span>
          <small>with roster placements</small>
        </article>
        <article className="kpi">
          <strong>{collab}</strong>
          <span>Collab playlists</span>
          <small>with roster placements</small>
        </article>
      </div>
      <div className="chart-grid">
        <BarChart
          title="Tracks on each playlist"
          caption="How many roster tracks sit on that playlist in this snapshot."
          bars={playlistBars.map((bar) => ({ label: bar.name, value: bar.count }))}
        />
        <BarChart
          title="Best slot on each playlist"
          caption="Longer bar means a higher slot. 1 is the top of the playlist."
          bars={playlistBars.map((bar) => ({
            label: bar.name,
            value: playlistBars.reduce((max, item) => Math.max(max, item.best), 1) - bar.best + 1,
            detail: `#${bar.best}`,
          }))}
        />
      </div>
      <div className="toolbar">
        <input
          className="search"
          placeholder="Search artists, playlists or tracks..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select value={artistFilter} onChange={(e) => setArtistFilter(e.target.value)}>
          <option value="all">All artists</option>
          {artists.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>
      <div className="groups">
        {groups.map((g) => {
          const id = g.name;
          const expanded = open[id] !== false;
          return (
            <section key={id} className="group">
              <button
                type="button"
                className="group-head"
                onClick={() => setOpen((prev) => ({ ...prev, [id]: !expanded }))}
              >
                <Avatar src={g.image} name={g.name} />
                <div>
                  <strong>{g.name}</strong>
                  <span className="muted">
                    {g.rows.length} playlist placement{g.rows.length === 1 ? "" : "s"}
                  </span>
                </div>
                <span className="badge">Best position #{g.best}</span>
                <span className="chevron">{expanded ? "▾" : "▸"}</span>
              </button>
              {expanded ? (
                <table>
                  <thead>
                    <tr>
                      <th>Playlist</th>
                      <th>Track</th>
                      <th>Position</th>
                    </tr>
                  </thead>
                  <tbody>
                    {g.rows.map((row) => (
                      <tr key={`${row.spotify_playlist_id}-${row.spotify_track_id}`}>
                        <td>{row.playlist_name}</td>
                        <td>{row.track_name}</td>
                        <td>
                          <span className={`pos pos-${row.position === 1 ? "best" : row.position <= 5 ? "good" : "rest"}`}>
                            {row.position}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}
            </section>
          );
        })}
      </div>
    </>
  );
}
