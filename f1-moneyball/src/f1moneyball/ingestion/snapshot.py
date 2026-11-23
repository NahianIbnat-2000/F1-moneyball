"""Constructor standings snapshot (Jolpica-F1, retrieved 19 November 2026).

Used only until the automated pipeline pull runs: the build workspace could not reach the
API, so final standings for 2010-2025 were retrieved with a web-fetch tool and saved with
provenance in data/manual/jolpica_constructor_standings_snapshot.csv. They pass four checks
(see tests/test_snapshot.py): wins sum to rounds, positions consecutive, points non-increasing,
and season point totals equal the points-system arithmetic where it is deterministic.

The snapshot holds standings only. Race-level variables (podiums, reliability, qualifying,
grid-to-finish) stay blank until the full API pull. Never edit values by hand.
"""
from __future__ import annotations

import pandas as pd

from f1moneyball.standardization.teams import add_team_id, team_display_names
from f1moneyball.utils import config
from f1moneyball.utils.config import regulatory_period

SNAPSHOT = "jolpica_constructor_standings_snapshot.csv"
SOURCE_LABEL = "Jolpica-F1 final standings snapshot, 19 Nov 2026 (standings only)"


def load_snapshot() -> pd.DataFrame:
    return pd.read_csv(config.MANUAL_DIR / SNAPSHOT)


def constructor_season_from_snapshot(snap: pd.DataFrame | None = None) -> pd.DataFrame:
    s = add_team_id(load_snapshot() if snap is None else snap)
    cs = s[["season", "team_id", "constructor_id", "constructor_name", "position", "points", "wins"]].copy()
    cs["races_entered"] = s["round"]
    cs["points_share"] = cs["points"] / cs.groupby("season")["points"].transform("sum")
    cs["points_per_race"] = cs["points"] / cs["races_entered"]
    cs["team_name"] = cs["team_id"].map(team_display_names())
    cs["regulatory_period"] = cs["season"].map(regulatory_period)
    cs["data_source"] = SOURCE_LABEL
    return cs.sort_values(["season", "position"]).reset_index(drop=True)
