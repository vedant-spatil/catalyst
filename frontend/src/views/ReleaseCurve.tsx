import { useEffect, useMemo, useState } from "react";
import Avatar from "../Avatar";
import LineChart from "../LineChart";
import { getJson } from "../api";
import { formatDate } from "../format";
import type { ReleaseCurveRow } from "../types";
import PageIntro from "../PageIntro";
import EmptyState from "./EmptyState";

export default function ReleaseCurve() {
  const [rows, setRows] = useState<ReleaseCurveRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [trackId, setTrackId] = useState("");
  const [viewBy, setViewBy] = useState<"days" | "snapshot">("days");

  useEffect(() => {
    getJson<ReleaseCurveRow[]>("/release-curve")
      .then((data) => {
        setRows(data);
        if (data[0]) setTrackId(data[0].spotify_track_id);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const tracks = useMemo(() => {
    if (!rows) return [];
    const seen = new Map<string, string>();
    for (const row of rows) {
      if (!seen.has(row.spotify_track_id)) seen.set(row.spotify_track_id, row.track_name);
    }
    return [...seen.entries()];
  }, [rows]);

  const selected = useMemo(() => {
    if (!rows) return [];
    return rows
      .filter((r) => r.spotify_track_id === trackId)
      .sort((a, b) => a.snapshot_date.localeCompare(b.snapshot_date));
  }, [rows, trackId]);

  const latestByTrack = useMemo(() => {
    if (!rows) return [];
    const map = new Map<string, ReleaseCurveRow>();
    for (const row of rows) {
      const prev = map.get(row.spotify_track_id);
      if (!prev || row.snapshot_date > prev.snapshot_date) map.set(row.spotify_track_id, row);
    }
    return [...map.values()].sort((a, b) => a.track_name.localeCompare(b.track_name));
  }, [rows]);

  if (error) return <p className="banner error">{error}</p>;
  if (!rows) return <p className="banner">Loading...</p>;
  if (rows.length === 0) {
    return (
      <EmptyState
        title="No release data available"
        description="A track needs a day-precision release date and a committed snapshot."
      />
    );
  }

  const meta = selected[selected.length - 1] || selected[0];
  const points = selected
    .map((r) => {
      if (viewBy === "days") {
        if (r.days_since_release == null) return null;
        return {
          x: r.days_since_release,
          yCount: r.playlist_count,
          yPos: r.best_position,
          label: String(r.days_since_release),
        };
      }
      const day = Number(r.snapshot_date.slice(8, 10));
      return {
        x: Date.parse(r.snapshot_date.slice(0, 10)),
        yCount: r.playlist_count,
        yPos: r.best_position,
        label: String(day),
      };
    })
    .filter((p): p is NonNullable<typeof p> => p != null);

  return (
    <>
      <PageIntro
        eyebrow="RELEASE PERFORMANCE"
        title="Release Curve"
        description="Playlist count is how many watched playlists include the track. Best position is its highest slot. 1 is the top of the playlist."
        extra={
          <div className="controls">
            <label className="control">
              Select track
              <select value={trackId} onChange={(e) => setTrackId(e.target.value)}>
                {tracks.map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </select>
            </label>
            <label className="control">
              View by
              <select value={viewBy} onChange={(e) => setViewBy(e.target.value as "days" | "snapshot")}>
                <option value="days">Days since release</option>
                <option value="snapshot">Snapshot date</option>
              </select>
            </label>
          </div>
        }
      />
      <div className="split-card">
        {meta ? (
          <aside className="meta-panel">
            <Avatar src={null} name={meta.track_name} />
            <h3>{meta.track_name}</h3>
            <p className="muted">{meta.artist_name || "Unknown artist"}</p>
            <dl>
              <div>
                <dt>Release date</dt>
                <dd>{meta.release_date ? formatDate(meta.release_date) : "Unknown days"}</dd>
              </div>
              <div>
                <dt>Days since release</dt>
                <dd>{meta.days_since_release == null ? "Unknown days" : meta.days_since_release}</dd>
              </div>
              <div>
                <dt>Latest snapshot</dt>
                <dd>{formatDate(meta.snapshot_date)}</dd>
              </div>
            </dl>
            <p className="legend">
              <span className="swatch count" /> Playlist count
              <span className="swatch pos" /> Best position (lower is better)
            </p>
          </aside>
        ) : null}
        <div className="chart-wrap">
          <LineChart points={points} showCount showPos />
        </div>
      </div>
      <h3 className="section-title">All tracks (latest snapshot)</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Track</th>
              <th>Artist</th>
              <th>Days since release</th>
              <th>Playlist count</th>
              <th>Best position</th>
            </tr>
          </thead>
          <tbody>
            {latestByTrack.map((row) => (
              <tr key={row.spotify_track_id}>
                <td>{row.track_name}</td>
                <td>{row.artist_name || "Unknown artist"}</td>
                <td>{row.days_since_release == null ? "Unknown days" : row.days_since_release}</td>
                <td>{row.playlist_count}</td>
                <td>{row.best_position ?? "n/a"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
