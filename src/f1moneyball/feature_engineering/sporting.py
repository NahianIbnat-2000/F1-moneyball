"""Build analysis tables from parsed, standardized sporting data."""
from __future__ import annotations

import numpy as np
import pandas as pd

from f1moneyball.standardization.teams import classify_status, team_display_names
from f1moneyball.utils.config import regulatory_period


def enrich_results(results: pd.DataFrame) -> pd.DataFrame:
    df = results.copy()
    df["status_class"] = df["status"].map(classify_status)
    df["classified"] = df["status_class"].eq("finished")
    df["is_mechanical_dnf"] = df["status_class"].eq("mechanical")
    # Grid 0 means pit-lane start in Ergast data; treat it as last on the grid for that race.
    n_cars = df.groupby(["season", "round"])["driver_id"].transform("count")
    grid = df["grid"].where(df["grid"] > 0, n_cars)
    df["grid_to_finish"] = np.where(df["classified"], grid - df["position"], np.nan)
    return df


def gap_to_pole(qualifying: pd.DataFrame) -> pd.DataFrame:
    """Percentage gap of each driver's best time to the fastest time of that session."""
    df = qualifying.copy()
    pole = df.groupby(["season", "round"])["best_ms"].transform("min")
    df["gap_to_pole_pct"] = (df["best_ms"] / pole - 1) * 100
    return df


def constructor_season(standings: pd.DataFrame, results: pd.DataFrame,
                       qualifying: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per (season, team_id). Points come from the official final standings,
    not from summing race results, because sprint and penalty adjustments live there."""
    st = standings.sort_values("round").groupby(["season", "constructor_id"]).tail(1)
    cs = st[["season", "team_id", "constructor_id", "constructor_name", "position", "points", "wins"]].copy()

    res = enrich_results(results)
    agg = res.groupby(["season", "team_id"]).agg(
        races_entered=("round", "nunique"),
        car_starts=("driver_id", "size"),
        podiums=("position", lambda s: int((s <= 3).sum())),
        classified_finishes=("classified", "sum"),
        mechanical_dnfs=("is_mechanical_dnf", "sum"),
        mean_grid_to_finish=("grid_to_finish", "mean"),
    ).reset_index()
    cs = cs.merge(agg, on=["season", "team_id"], how="left")

    if qualifying is not None and not qualifying.empty:
        q = gap_to_pole(qualifying)
        # Team's best car per session, then median across the season (robust to one bad session).
        best = q.groupby(["season", "round", "team_id"])["gap_to_pole_pct"].min().reset_index()
        qagg = best.groupby(["season", "team_id"]).agg(
            median_quali_gap_pct=("gap_to_pole_pct", "median"),
            poles=("gap_to_pole_pct", lambda s: int((s == 0).sum())),
        ).reset_index()
        cs = cs.merge(qagg, on=["season", "team_id"], how="left")

    season_points = cs.groupby("season")["points"].transform("sum")
    cs["points_share"] = cs["points"] / season_points
    cs["points_per_race"] = cs["points"] / cs["races_entered"]
    cs["completion_rate"] = cs["classified_finishes"] / cs["car_starts"]
    cs["mechanical_dnf_rate"] = cs["mechanical_dnfs"] / cs["car_starts"]
    cs["team_name"] = cs["team_id"].map(team_display_names())
    cs["regulatory_period"] = cs["season"].map(regulatory_period)
    return cs.sort_values(["season", "position"]).reset_index(drop=True)
