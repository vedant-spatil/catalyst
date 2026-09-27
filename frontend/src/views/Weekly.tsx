import { useEffect, useMemo, useState } from "react";
import Avatar from "../Avatar";
import LineChart from "../LineChart";
import Sparkline from "../Sparkline";
import { getJson } from "../api";
import { weekLabel } from "../format";
import type { WeeklyRow } from "../types";
import PageIntro from "../PageIntro";
import EmptyState from "./EmptyState";

export default function Weekly() {
  const [rows, setRows] = useState<WeeklyRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [artistId, setArtistId] = useState("");
  const [metric, setMetric] = useState<"both" | "count" | "pos">("both");

  useEffect(() => {
    getJson<WeeklyRow[]>("/weekly")
      .then((data) => {
        setRows(data);
        if (data[0]) setArtistId(data[0].spotify_artist_id);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const artists = useMemo(() => {
    if (!rows) return [];
    const map = new Map<string, string>();
    for (const row of rows) map.set(row.spotify_artist_id, row.artist_name);
    return [...map.entries()];
  }, [rows]);

  const weeks = useMemo(() => {
    if (!rows) return [];
    const keys = new Set(rows.map((r) => `${r.iso_year}-${r.iso_week}`));
    return [...keys]
      .map((k) => {
        const [y, w] = k.split("-").map(Number);
        return { iso_year: y, iso_week: w };
      })
      .sort((a, b) => a.iso_year - b.iso_year || a.iso_week - b.iso_week);
  }, [rows]);

  const latestWeeks = weeks.slice(-5);

  const series = useMemo(() => {
    if (!rows) return [];
    return rows
      .filter((r) => r.spotify_artist_id === artistId)
      .sort((a, b) => a.iso_year - b.iso_year || a.iso_week - b.iso_week);
  }, [rows, artistId]);

  if (error) return <p className="banner error">{error}</p>;
  if (!rows) return <p className="banner">Loading...</p>;
  if (rows.length === 0) {
    return (
      <EmptyState
        title="Not enough weekly data"
        description="Weekly trends appear once two ISO weeks are available."
      />
    );
  }

  const latest = series[series.length - 1];
  const points = series.map((r) => ({
    x: r.iso_year * 100 + r.iso_week,
    yCount: r.playlist_count,
    yPos: r.best_position,
    label: weekLabel(r.iso_year, r.iso_week),
  }));

  return (
    <>
      <PageIntro
        eyebrow="WEEKLY TRENDS"
        title="Weekly Trends"
        description="Each point is one ISO week. Playlist count is placements that week. Best position is the highest slot, and 1 is the top."
        extra={
          <div className="controls">
            <label className="control">
              Select artist
              <select value={artistId} onChange={(e) => setArtistId(e.target.value)}>
                {artists.map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </select>
            </label>
            <label className="control">
              Metric
              <select value={metric} onChange={(e) => setMetric(e.target.value as "both" | "count" | "pos")}>
                <option value="both">Both</option>
                <option value="count">Playlist count</option>
                <option value="pos">Best position</option>
              </select>
            </label>
          </div>
        }
      />
      <div className="split-card">
        {latest ? (
          <aside className="meta-panel">
            <Avatar src={null} name={latest.artist_name} />
            <h3>{latest.artist_name}</h3>
            <p className="muted">{latest.playlist_count} playlist placements latest snapshot</p>
            <dl>
              <div>
                <dt>Best position</dt>
                <dd className="big">#{latest.best_position ?? "n/a"}</dd>
              </div>
              <div>
                <dt>Playlist count</dt>
                <dd className="big">{latest.playlist_count}</dd>
              </div>
            </dl>
          </aside>
        ) : null}
        <div className="chart-wrap">
          <LineChart points={points} showCount={metric !== "pos"} showPos={metric !== "count"} />
        </div>
      </div>
      <h3 className="section-title">All artists (latest weeks)</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Artist</th>
              {latestWeeks.map((w) => (
                <th key={`${w.iso_year}-${w.iso_week}`}>{weekLabel(w.iso_year, w.iso_week)}</th>
              ))}
              <th>Trend</th>
            </tr>
          </thead>
          <tbody>
            {artists.map(([id, name]) => {
              const byWeek = rows.filter((r) => r.spotify_artist_id === id);
              const values = latestWeeks.map((w) => {
                const hit = byWeek.find((r) => r.iso_year === w.iso_year && r.iso_week === w.iso_week);
                return hit ? hit.playlist_count : 0;
              });
              return (
                <tr key={id}>
                  <td>{name}</td>
                  {values.map((v, i) => (
                    <td key={i}>{v}</td>
                  ))}
                  <td>
                    <Sparkline values={values} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
