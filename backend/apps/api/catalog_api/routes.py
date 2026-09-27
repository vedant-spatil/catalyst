from __future__ import annotations

from fastapi import APIRouter

from catalog_api.db import get_conn
from catalog_api.models import ExposureRow, MoverRow, ReleaseCurveRow, RunLog, WeeklyRow

router = APIRouter()


@router.get("/exposure", response_model=list[ExposureRow])
def exposure() -> list[ExposureRow]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM gold.mart_playlist_exposure ORDER BY artist_name, position").fetchall()
    return [ExposureRow.model_validate(dict(row)) for row in rows]


@router.get("/release-curve", response_model=list[ReleaseCurveRow])
def release_curve() -> list[ReleaseCurveRow]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM gold.mart_release_curve ORDER BY snapshot_date, track_name").fetchall()
    return [ReleaseCurveRow.model_validate(dict(row)) for row in rows]


@router.get("/movers", response_model=list[MoverRow])
def movers() -> list[MoverRow]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM gold.mart_movers_losers ORDER BY change, track_name").fetchall()
    return [MoverRow.model_validate(dict(row)) for row in rows]


@router.get("/weekly", response_model=list[WeeklyRow])
def weekly() -> list[WeeklyRow]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM gold.mart_weekly_movement ORDER BY iso_year, iso_week, artist_name"
        ).fetchall()
    return [WeeklyRow.model_validate(dict(row)) for row in rows]


@router.get("/runs/latest", response_model=RunLog | None)
def latest_run() -> RunLog | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM ops.run_log ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        return None
    return RunLog.model_validate(dict(row))
