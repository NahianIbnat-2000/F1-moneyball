"""Resources and performance: pooled OLS, team fixed effects, two-way fixed effects.

Specification (per financial metric, one currency at a time):
    points_share_it = b * log(resource_{i,t-1}) [+ team effects] [+ season effects] + e_it

* The regressor is lagged one season: success raises prize money and sponsorship, so a
  same-season link would partly run from points to money. Lagging reduces, but does not
  remove, that problem. Results are ASSOCIATIONS, not causal effects.
* Standard errors are clustered by team. With few teams (clusters) they are unreliable;
  the number of clusters is reported with every model and flagged below 10.
* Inference reported for every model: the clustered standard error; p-value and 95% interval from the t
  distribution with G - 1 degrees of freedom (G = number of teams; `p_t`, `ci_t_low`, `ci_t_high`); and, for the
  two fixed-effects models, the restricted wild cluster bootstrap p-value (`p_wild`) with the bootstrap interval
  obtained by inverting the same test (`ci_boot_low`, `ci_boot_high`). `p_value`, `ci_low` and `ci_high` use the
  normal distribution and are kept for comparison with earlier versions.
* `effect_10pct_pp`: change in points share, in percentage points, associated with 10% more
  resources the previous season = b * ln(1.1) * 100.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from f1moneyball.econometrics.inference import WildCluster

MIN_OBS, MIN_TEAMS, MIN_SEASONS = 20, 4, 3

SPECS = [
    ("pooled", "Pooled OLS", "points_share ~ log_resource_lag"),
    ("team_fe", "Team fixed effects", "points_share ~ log_resource_lag + C(team_id)"),
    ("twfe", "Team and season fixed effects", "points_share ~ log_resource_lag + C(team_id) + C(season)"),
]


def lagged_panel(eff: pd.DataFrame, metric: str, currency: str) -> pd.DataFrame:
    reason = eff["exclusion_reason"].fillna("")
    d = eff[(eff["metric"] == metric) & (eff["currency"] == currency)
            & (eff["exclusion_reason"].isna() | reason.str.startswith("Only"))]
    # Lag uses any usable figure for the team, even if its season group was too small to
    # compute shares: the regression does not need shares of resources.
    d = d[d["value"] > 0][["team_id", "season", "value", "points_share"]].drop_duplicates(["team_id", "season"])
    d = d.sort_values(["team_id", "season"])
    d["log_resource"] = np.log(d["value"])
    prev = d[["team_id", "season", "log_resource"]].copy()
    prev["season"] += 1
    out = d.drop(columns="log_resource").merge(prev.rename(columns={"log_resource": "log_resource_lag"}),
                                                on=["team_id", "season"], how="inner")
    return out.dropna(subset=["points_share", "log_resource_lag"])


def run_models(eff: pd.DataFrame, wild: bool = True) -> pd.DataFrame:
    rows = []
    usable = eff[eff["value"] > 0]
    for metric, g in usable.groupby("metric"):
        currency = g["currency"].mode().iat[0]
        panel = lagged_panel(eff, metric, currency)
        n, n_teams, n_seasons = len(panel), panel["team_id"].nunique(), panel["season"].nunique()
        base = {"metric": metric, "currency": currency, "outcome": "points_share",
                "regressor": f"log({metric}) previous season", "n_obs": n, "n_teams": n_teams,
                "n_seasons": n_seasons}
        if n < MIN_OBS or n_teams < MIN_TEAMS or n_seasons < MIN_SEASONS:
            for mid, label, formula in SPECS:
                rows.append({**base, "model_id": f"{metric}_{mid}", "specification": label, "formula": formula,
                             "estimated": False,
                             "note": (f"Not estimated: needs at least {MIN_OBS} observations, {MIN_TEAMS} teams "
                                      f"and {MIN_SEASONS} seasons with a lagged figure "
                                      f"(has {n}, {n_teams}, {n_seasons}).")})
            continue
        for mid, label, formula in SPECS:
            clusters = panel["team_id"].astype("category").cat.codes
            fit = smf.ols(formula, data=panel).fit(cov_type="cluster", cov_kwds={"groups": clusters})
            b, se = fit.params["log_resource_lag"], fit.bse["log_resource_lag"]
            lo, hi = fit.conf_int().loc["log_resource_lag"]
            note = "Association, not a causal effect."
            if n_teams < 10:
                note += f" Only {n_teams} clusters: clustered standard errors may be too small."
            rows.append({**base, "model_id": f"{metric}_{mid}", "specification": label, "formula": formula,
                         "estimated": True, "coef": float(b), "se": float(se),
                         "ci_low": float(lo), "ci_high": float(hi),
                         "p_value": float(fit.pvalues["log_resource_lag"]), "r2": float(fit.rsquared),
                         "effect_10pct_pp": float(b * np.log(1.1) * 100), "se_type": "clustered by team",
                         **small_sample(float(b), float(se), n_teams),
                         **(bootstrap(formula, panel) if wild and mid != "pooled" else {}),
                         "note": note})
    return pd.DataFrame(rows)


def small_sample(b: float, se: float, G: int) -> dict:
    """p-value and 95% interval with t(G - 1) critical values (Cameron and Miller 2015)."""
    if not se > 0 or G < 2:
        return {"p_t": np.nan, "ci_t_low": np.nan, "ci_t_high": np.nan}
    c = stats.t.ppf(0.975, G - 1)
    return {"p_t": float(2 * stats.t.sf(abs(b / se), G - 1)), "ci_t_low": b - c * se, "ci_t_high": b + c * se}


def bootstrap(formula: str, panel: pd.DataFrame) -> dict:
    """Restricted wild cluster bootstrap p-value at zero and the 95% interval from inverting the same test."""
    w = WildCluster(formula, panel, "log_resource_lag", "team_id")
    lo, hi = w.ci()
    return {"p_wild": w.p_value(0.0), "ci_boot_low": lo, "ci_boot_high": hi}
