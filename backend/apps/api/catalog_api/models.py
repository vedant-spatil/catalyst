from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ExposureRow(BaseModel):
    snapshot_date: date
    spotify_artist_id: str | None
    artist_name: str | None
    spotify_playlist_id: str
    playlist_name: str
    spotify_track_id: str
    track_name: str
    position: int
    collaborative: bool = False
    artist_image_url: str | None = None


class ReleaseCurveRow(BaseModel):
    snapshot_date: date
    spotify_track_id: str
    track_name: str
    days_since_release: int | None
    playlist_count: int
    best_position: int | None
    artist_name: str | None = None
    release_date: date | None = None


class MoverRow(BaseModel):
    from_snapshot: date
    to_snapshot: date
    spotify_track_id: str
    track_name: str
    change: Literal["added", "dropped"]
    artist_name: str | None = None
    playlist_names: list[str] = Field(default_factory=list)


class WeeklyRow(BaseModel):
    iso_year: int
    iso_week: int
    spotify_artist_id: str
    artist_name: str
    best_position: int | None
    playlist_count: int


class RunLog(BaseModel):
    run_id: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    command: str
    snapshot_date: date | None
    row_counts: dict
    error_list: list
