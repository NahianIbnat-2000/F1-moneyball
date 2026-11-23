"""Competitive balance indicators, computed per season from constructor points.

All functions take a 1-D array of non-negative points for the teams in one season.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from f1moneyball.utils.config import regulatory_period


def shares(points) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    total = p.sum()
    if total <= 0:
        raise ValueError("Total points must be positive")
    return p / total


def hhi(points) -> float:
    """Herfindahl-Hirschman Index on the 0-1 scale (1/N = perfect balance, 1 = monopoly)."""
    s = shares(points)
    return float((s ** 2).sum())


def hhi_normalized(points) -> float:
    """(HHI - 1/N) / (1 - 1/N). Removes the mechanical effect of grid size, which varies
    from 10 to 12 teams across 2010-2025. 0 = equal shares, 1 = one team scores everything."""
    n = len(points)
    return (hhi(points) - 1 / n) / (1 - 1 / n)


def gini(points) -> float:
    x = np.sort(np.asarray(points, dtype=float))
    n = len(x)
    if x.sum() == 0:
        return 0.0
    cum = np.cumsum(x)
    return float((n + 1 - 2 * (cum / cum[-1]).sum()) / n)


def coefficient_of_variation(points) -> float:
    p = np.asarray(points, dtype=float)
    return float(p.std(ddof=0) / p.mean())


def top_k_share(points, k: int = 3) -> float:
    s = np.sort(shares(points))[::-1]
    return float(s[:k].sum())


def balance_table(cs: pd.DataFrame) -> pd.DataFrame:
    """One row per season. `cs` is the constructor_season table."""
    rows = []
    prev: pd.Series | None = None
    for season, g in cs.sort_values("season").groupby("season"):
        pts = g["points"].to_numpy()
        row = {
            "season": int(season), "n_teams": len(g),
            "hhi": hhi(pts), "hhi_normalized": hhi_normalized(pts), "gini": gini(pts),
            "cv": coefficient_of_variation(pts), "sd_points": float(np.std(pts)),
            "top3_share": top_k_share(pts, 3),
            "winner_share_of_wins": float(g["wins"].max() / g["wins"].sum()) if g["wins"].sum() else np.nan,
            "leader_points_share": float(g["points_share"].max()),
        }
        # Rank persistence: Spearman correlation of finishing rank with last season's rank,
        # for lineages present in both seasons. High = the order rarely changes.
        cur = g.set_index("team_id")["position"]
        if prev is not None:
            common = cur.index.intersection(prev.index)
            if len(common) >= 4:
                rho, _ = spearmanr(cur[common], prev[common])
                row["rank_persistence"] = float(rho)
                row["mean_abs_rank_change"] = float((cur[common] - prev[common]).abs().mean())
        prev = cur
        row["regulatory_period"] = regulatory_period(int(season))
        rows.append(row)
    return pd.DataFrame(rows)
