import { useEffect, useMemo, useState } from "react";
import BarChart from "../BarChart";
import { getJson } from "../api";
import { formatDate } from "../format";
import type { MoverRow } from "../types";
import PageIntro from "../PageIntro";
import EmptyState from "./EmptyState";

export default function Movers() {
  const [rows, setRows] = useState<MoverRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJson<MoverRow[]>("/movers")
      .then(setRows)
      .catch((err: Error) => setError(err.message));
  }, []);

  const added = useMemo(() => (rows || []).filter((r) => r.change === "added"), [rows]);
  const dropped = useMemo(() => (rows || []).filter((r) => r.change === "dropped"), [rows]);

  if (error) return <p className="banner error">{error}</p>;
  if (!rows) return <p className="banner">Loading...</p>;
  if (rows.length === 0) {
    return (
      <EmptyState
        title="No playlist movements yet"
        description="A second snapshot date is required before added or dropped tracks can be calculated."
      />
    );
  }

  const from = rows[0].from_snapshot;
  const to = rows[0].to_snapshot;

  return (
    <>
      <PageIntro
        eyebrow="PLAYLIST MOVERS"
        title="Playlist Movers"
        description="Tracks added or dropped between the two latest snapshot dates."
        extra={
          <div className="date-compare">
            <div>
              <span>From</span>
              <strong>{formatDate(from)}</strong>
            </div>
            <span className="arrow">→</span>
            <div>
              <span>To</span>
              <strong>{formatDate(to)}</strong>
            </div>
          </div>
        }
      />
      <div className="kpis two">
        <article className="kpi added">
          <strong>{added.length}</strong>
          <span>Added</span>
          <small>new playlist placements</small>
        </article>
        <article className="kpi dropped">
          <strong>{dropped.length}</strong>
          <span>Dropped</span>
          <small>no longer in playlists</small>
        </article>
      </div>
      <BarChart
        title="Added and dropped"
        caption={`Membership changes from ${formatDate(from)} to ${formatDate(to)}. A track counts once even if it moved on more than one playlist.`}
        bars={[
          { label: "Added", value: added.length },
          { label: "Dropped", value: dropped.length },
        ]}
      />
      <div className="two-col">
        <section className="tint-added">
          <h3>Added Tracks ({added.length})</h3>
          <table>
            <thead>
              <tr>
                <th>Track</th>
                <th>Artist</th>
                <th>Added to</th>
              </tr>
            </thead>
            <tbody>
              {added.map((row) => (
                <tr key={`a-${row.spotify_track_id}`}>
                  <td>{row.track_name}</td>
                  <td>{row.artist_name || "Unknown artist"}</td>
                  <td>{(row.playlist_names || []).join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="tint-dropped">
          <h3>Dropped Tracks ({dropped.length})</h3>
          <table>
            <thead>
              <tr>
                <th>Track</th>
                <th>Artist</th>
                <th>Removed from</th>
              </tr>
            </thead>
            <tbody>
              {dropped.map((row) => (
                <tr key={`d-${row.spotify_track_id}`}>
                  <td>{row.track_name}</td>
                  <td>{row.artist_name || "Unknown artist"}</td>
                  <td>{(row.playlist_names || []).join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </>
  );
}
