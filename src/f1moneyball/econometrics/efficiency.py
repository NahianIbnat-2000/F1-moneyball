"""Financial panel and descriptive efficiency indicators.

Rules that protect comparability:
  * One financial measure (`metric`) at a time. Different measures are never combined.
  * Shares are computed within a comparison group = (season, metric, currency).
    No currency conversion is done here, so teams reporting in different currencies
    are never put in the same denominator.
  * A group needs at least `min_teams` teams, otherwise its rows are kept but excluded,
    with the reason written in `exclusion_reason`.
  * Only RESOURCE measures enter the panel. Profit measures (operating profit, profit before
    tax) are outcomes, can be negative and have no meaningful share, so they stay in
    financial_observation but are not used here.
  * Headcount is a count of people, not money: its `currency` is set to "persons" so it never
    shares a comparison group with a currency, and points per million is not computed for it.
  * Points share is recomputed within the group (team points / points of the teams in the
    group), so both shares refer to the same set of teams.

These are DESCRIPTIVE ratios. They are not estimates of technical efficiency and say
nothing about causation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SOURCE_RANK = {"audited": 0, "official_disclosure": 1, "secondary_estimate": 2, "derived_estimate": 3}
REPORTED = {"audited", "official_disclosure"}
RESOURCE_METRICS = {"revenue", "turnover", "operating_costs", "staff_costs", "estimated_budget",
                    "sponsorship_revenue", "headcount"}
COUNT_METRICS = {"headcount"}
PERSONS = "persons"

SPORT_COLS = ["points", "points_share", "position", "wins", "podiums", "completion_rate",
              "mechanical_dnf_rate", "mean_grid_to_finish", "median_quali_gap_pct", "team_name"]


def financial_panel(fin: pd.DataFrame, cs: pd.DataFrame) -> pd.DataFrame:
    """Join usable financial figures to constructor seasons. One row per team, season, metric."""
    f = fin[(fin["source_class"] != "missing") & fin["metric"].isin(RESOURCE_METRICS)].copy()
    f.loc[f["metric"].isin(COUNT_METRICS), "currency"] = PERSONS
    f["value"] = pd.to_numeric(f["value"], errors="coerce")
    f = f.dropna(subset=["value", "season_mapped"])
    f["season"] = f["season_mapped"].astype(int)
    f["exclusion_reason"] = None
    # Two legal entities for the same team, season and metric cannot both be the team's figure.
    dup = f.duplicated(["team_id", "season", "metric"], keep=False)
    f.loc[dup, "exclusion_reason"] = "More than one entity reports this metric for the team and season"
    keep = ["team_id", "season", "metric", "value", "currency", "source_class", "confidence",
            "entity_name", "financial_year_end", "exclusion_reason"]
    panel = f[keep].merge(cs[["season", "team_id", *[c for c in SPORT_COLS if c in cs.columns]]],
                          on=["season", "team_id"], how="left")
    no_sport = panel["points"].isna() & panel["exclusion_reason"].isna()
    panel.loc[no_sport, "exclusion_reason"] = "No sporting record for this team and season"
    panel["is_reported"] = panel["source_class"].isin(REPORTED)
    return panel.sort_values(["metric", "season", "team_id"]).reset_index(drop=True)


def efficiency_table(panel: pd.DataFrame, min_teams: int = 4) -> pd.DataFrame:
    df = panel.copy()
    for c in ["group_n_teams", "resource_share", "points_share_in_group", "efficiency_ratio",
              "points_per_million", "resource_rank", "points_rank", "rank_gap"]:
        df[c] = np.nan
    usable = df["exclusion_reason"].isna()
    for (season, metric, ccy), g in df[usable].groupby(["season", "metric", "currency"]):
        idx = g.index
        n = len(g)
        df.loc[idx, "group_n_teams"] = n
        other_ccy = df[(df["season"] == season) & (df["metric"] == metric) & usable & (df["currency"] != ccy)]
        if n < min_teams:
            why = f"Only {n} teams report {metric} in {ccy} for {season}; at least {min_teams} are needed"
            if len(other_ccy):
                why += " (other teams report in a different currency; no conversion is applied)"
            df.loc[idx, "exclusion_reason"] = why
            continue
        if (g["value"] <= 0).any():
            df.loc[idx, "exclusion_reason"] = "Shares need positive values; this measure has zero or negative values"
            continue
        res_share = g["value"] / g["value"].sum()
        pts_total = g["points"].sum()
        pts_share = g["points"] / pts_total if pts_total > 0 else np.nan
        df.loc[idx, "resource_share"] = res_share
        df.loc[idx, "points_share_in_group"] = pts_share
        df.loc[idx, "efficiency_ratio"] = pts_share / res_share
        if ccy != PERSONS:
            df.loc[idx, "points_per_million"] = g["points"] / (g["value"] / 1e6)
        df.loc[idx, "resource_rank"] = g["value"].rank(ascending=False, method="min")
        df.loc[idx, "points_rank"] = g["points"].rank(ascending=False, method="min")
        # Positive rank_gap: the team finished higher on points than its resource rank.
        df.loc[idx, "rank_gap"] = df.loc[idx, "resource_rank"] - df.loc[idx, "points_rank"]
    df["included"] = df["exclusion_reason"].isna()
    return df
