export type ExposureRow = {
  snapshot_date: string;
  spotify_artist_id: string | null;
  artist_name: string | null;
  spotify_playlist_id: string;
  playlist_name: string;
  spotify_track_id: string;
  track_name: string;
  position: number;
  collaborative: boolean;
  artist_image_url: string | null;
};

export type ReleaseCurveRow = {
  snapshot_date: string;
  spotify_track_id: string;
  track_name: string;
  days_since_release: number | null;
  playlist_count: number;
  best_position: number | null;
  artist_name: string | null;
  release_date: string | null;
};

export type MoverRow = {
  from_snapshot: string;
  to_snapshot: string;
  spotify_track_id: string;
  track_name: string;
  change: "added" | "dropped";
  artist_name: string | null;
  playlist_names: string[];
};

export type WeeklyRow = {
  iso_year: number;
  iso_week: number;
  spotify_artist_id: string;
  artist_name: string;
  best_position: number | null;
  playlist_count: number;
};

export type RunLog = {
  run_id: number;
  started_at: string;
  finished_at: string | null;
  status: string;
  command: string;
  snapshot_date: string | null;
  row_counts: Record<string, unknown>;
  error_list: unknown[];
};
