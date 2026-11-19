"""Robustness and sensitivity checks for the three studies, collected in one long table.

Every row is one estimate: which study and check it belongs to, the coefficient that matters, its
uncertainty, and a note. `baseline_coef` repeats the main result so a reader can see how much a
check moves it.

Few clusters. The resource models and the dose-response model have only six teams. Clustered
standard errors are too small with so few clusters (Cameron, Gelbach and Miller 2008), so the main
estimates also get a wild cluster bootstrap p-value: restricted (null imposed), Webb six-point weights,
which work better than Rademacher weights when there are fewer than about ten clusters (Webb 2023).

Results are associations or descriptive comparisons, never causal effects.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import patsy
import statsmodels.formula.api as smf

from f1moneyball.econometrics import cost_cap as cc
from f1moneyball.econometrics import gp_economy as gp
from f1moneyball.econometrics.models import lagged_panel

RESET_SEASONS = (2014, 2017, 2022)  # big technical rule changes
COVID_SEASONS = (2020, 2021)
METRICS = ("turnover", "staff_costs", "headcount")
SPECS = {"pooled": "", "team_fe": " + C(team_id)", "twfe": " + C(team_id) + C(season)"}
WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])
B_DRAWS = 9999
GOOD_FIT_MULTIPLE = 2.0  # placebo kept if its pre-entry RMSPE is at most this multiple of the host's


# ----------------------------------------------------------------------------- inference helpers
def _cluster_t(X: np.ndarray, y: np.ndarray, groups: np.ndarray, j: int) -> tuple[float, float]:
    """OLS coefficient j and its CR1 cluster-robust t statistic."""
    XtX_inv = np.linalg.pinv(X.T @ X)
    b = XtX_inv @ X.T @ y
    u = y - X @ b
    G = np.unique(groups)
    meat = np.zeros((X.shape[1], X.shape[1]))
    for g in G:
        s = X[groups == g].T @ u[groups == g]
        meat += np.outer(s, s)
    n, k = X.shape
    c = len(G) / (len(G) - 1) * (n - 1) / (n - k)
    V = c * XtX_inv @ meat @ XtX_inv
    return float(b[j]), float(b[j] / np.sqrt(V[j, j])) if V[j, j] > 0 else float("nan")


def wild_cluster_p(formula: str, data: pd.DataFrame, var: str, cluster: str, draws: int = B_DRAWS, seed: int = 20261119) -> float:
    """Two-sided wild cluster restricted bootstrap p-value for H0: coefficient on `var` = 0."""
    y, X = patsy.dmatrices(formula, data, return_type="dataframe")
    j = list(X.columns).index(var)
    groups = data.loc[X.index, cluster].to_numpy()
    yv, Xv = y.to_numpy().ravel(), X.to_numpy()
    _, t_obs = _cluster_t(Xv, yv, groups, j)
    Xr = np.delete(Xv, j, axis=1)  # restricted model: coefficient set to zero
    br = np.linalg.pinv(Xr) @ yv
    fitted, resid = Xr @ br, yv - Xr @ br
    G = np.unique(groups)
    idx = np.searchsorted(G, groups)
    rng = np.random.default_rng(seed)
    t_star = np.empty(draws)
    for d in range(draws):
        w = rng.choice(WEBB, size=len(G))[idx]
        t_star[d] = _cluster_t(Xv, fitted + resid * w, groups, j)[1]
    return float((np.abs(t_star) >= abs(t_obs)).mean())


def _fit(formula: str, data: pd.DataFrame, var: str) -> dict:
    groups = data["team_id"].astype("category").cat.codes
    fit = smf.ols(formula, data=data).fit(cov_type="cluster", cov_kwds={"groups": groups})
    lo, hi = fit.conf_int().loc[var]
    return {"coef": float(fit.params[var]), "se": float(fit.bse[var]), "ci_low": float(lo), "ci_high": float(hi),
            "p_value": float(fit.pvalues[var]), "r2": float(fit.rsquared), "n_obs": int(len(data)),
            "n_teams": int(data["team_id"].nunique())}


# ----------------------------------------------------------------------------- F1 Moneyball
def moneyball_checks(eff: pd.DataFrame, cs: pd.DataFrame, wild: bool = True) -> list[dict]:
    rows: list[dict] = []
    extra = cs[["team_id", "season", "position", "completion_rate", "mean_grid_to_finish"]]
    for metric in METRICS:
        g = eff[(eff["metric"] == metric) & (eff["value"] > 0)]
        if g.empty:
            continue
        panel = lagged_panel(eff, metric, g["currency"].mode().iat[0]).merge(extra, on=["team_id", "season"], how="left")
        if panel["team_id"].nunique() < 4:
            continue
        panel["cap"] = (panel["season"] >= cc.CAP_YEAR).astype(int)
        base = {"study": "does-money-buy-speed", "metric": metric}
        x = "log_resource_lag"
        for spec, fe in SPECS.items():
            f = f"points_share ~ {x}{fe}"
            b = _fit(f, panel, x)
            row = {**base, "check_id": "baseline", "check": "Baseline", "model": spec, **b, "baseline_coef": b["coef"]}
            if wild and spec != "pooled":
                row["p_wild"] = wild_cluster_p(f, panel, x, "team_id")
            rows.append(row)
            sub = panel[~panel["season"].isin(RESET_SEASONS)]
            rows.append({**base, "check_id": "no_reset_seasons", "check": "Without rule-reset seasons (2014, 2017, 2022)",
                         "model": spec, **_fit(f, sub, x), "baseline_coef": b["coef"]})
            rows.append({**base, "check_id": "position_outcome",
                         "check": "Outcome: championship position (negative = better)", "model": spec,
                         **_fit(f"position ~ {x}{fe}", panel.dropna(subset=["position"]), x), "baseline_coef": None})
            if spec != "pooled":
                ctrl = panel.dropna(subset=["completion_rate", "mean_grid_to_finish"])
                h4 = _fit(f"points_share ~ {x} + completion_rate + mean_grid_to_finish{fe}", ctrl, x)
                h4["note"] = f"R-squared {b['r2']:.3f} without the two controls, {h4['r2']:.3f} with them."
                rows.append({**base, "check_id": "h4_operations", "check": "H4: adding completion rate and grid-to-finish gains",
                             "model": spec, **h4, "baseline_coef": b["coef"]})
        # H3: is the link different under the cost cap?
        f3 = f"points_share ~ {x} + {x}:cap + C(team_id) + C(season)"
        h3 = _fit(f3, panel, f"{x}:cap")
        h3["note"] = "Interaction of lagged log resources with the cost-cap period (2021 on). Descriptive: every team was capped."
        if wild:
            h3["p_wild"] = wild_cluster_p(f3, panel, f"{x}:cap", "team_id")
        rows.append({**base, "check_id": "h3_cap_interaction", "check": "H3: change in the resource link under the cost cap",
                     "model": "twfe", **h3, "baseline_coef": None})
        # Leave one team out (two-way fixed effects).
        ftw = f"points_share ~ {x} + C(team_id) + C(season)"
        full = _fit(ftw, panel, x)["coef"]
        for team in sorted(panel["team_id"].unique()):
            r = _fit(ftw, panel[panel["team_id"] != team], x)
            rows.append({**base, "check_id": "leave_one_team_out", "check": f"Without {team}", "model": "twfe",
                         **r, "baseline_coef": full, "dropped": team})
    return rows


# ----------------------------------------------------------------------------- Cost Cap Paradox
def cost_cap_checks(balance: pd.DataFrame, cs: pd.DataFrame, eff: pd.DataFrame | None, wild: bool = True) -> list[dict]:
    rows: list[dict] = []
    base = {"study": "cost-cap-paradox"}
    b = balance[balance["season"] <= cc.LAST_SEASON]
    for y in cc.INDICATORS:
        d = b[["season", y]].dropna()
        full = cc._its_row(d, y, cc.CAP_YEAR, "A", "its")
        r = cc._its_row(d[d["season"] != 2020], y, cc.CAP_YEAR, "A", "its")
        rows.append({**base, "check_id": "its_no_2020", "check": "Interrupted time series without 2020 (COVID calendar)",
                     "metric": y, "model": "ITS spec A", "coef": r["level_change"], "se": r["se"], "ci_low": r["ci_low"],
                     "ci_high": r["ci_high"], "p_value": r["p_value"], "n_obs": r["n_seasons"],
                     "baseline_coef": full["level_change"]})
    if eff is None or eff.empty:
        return rows
    for metric, label in (("turnover", "turnover"), ("staff_costs", "staff costs")):
        panel, info = cc.exposure_panel(cs, eff[eff["metric"] == metric])
        if info["n_teams"] < cc.MIN_EXPOSED_TEAMS:
            continue
        f = "points_share ~ exposure:post + C(team_id) + C(season)"
        for check_id, check, data in (
            ("dose_" + metric, f"Dose-response, exposure from {label}", panel),
            ("dose_" + metric + "_no_covid", f"Dose-response, exposure from {label}, without 2020-2021",
             panel[~panel["season"].isin(COVID_SEASONS)]),
        ):
            r = _fit(f, data, "exposure:post")
            if wild:
                r["p_wild"] = wild_cluster_p(f, data, "exposure:post", "team_id")
            rows.append({**base, "check_id": check_id, "check": check, "metric": metric, "model": "team and season FE", **r})
    return rows


# ----------------------------------------------------------------------------- Grand Prix Economy
def grand_prix_checks(tourism: pd.DataFrame, events: pd.DataFrame, inference: pd.DataFrame | None) -> list[dict]:
    rows: list[dict] = []
    base = {"study": "grand-prix-economy"}
    if tourism.empty or events.empty:
        return rows
    for host, ev in events.groupby("region_id"):
        for series in sorted(tourism["series"].unique()):
            # (1) Same race months, other states: is the race-month rise specific to the host?
            for state, sg in tourism[tourism["region_id"] != host].groupby("region_id"):
                t = sg.assign(is_host=True)
                e = gp.event_study(t, ev.assign(region_id=state), series)
                k0 = e[(e["k"] == 0) & e["estimated"]]
                if len(k0):
                    r = k0.iloc[0]
                    rows.append({**base, "check_id": "placebo_state_race_month", "check": f"{r['region_name']}, host's race months",
                                 "metric": series, "model": "event study k=0", "coef": r["coef"], "se": r["se"],
                                 "ci_low": r["ci_low"], "ci_high": r["ci_high"], "pct_effect": r["pct_effect"],
                                 "n_obs": r["n_months"], "region": state})
            # (2) Host minus the rest of the country: race-month rise relative to the other states.
            d = tourism[tourism["series"] == series].copy()
            d["value"] = pd.to_numeric(d["value"], errors="coerce")
            others = d[d["region_id"] != host].groupby("month")["value"].sum()
            h = d[d["region_id"] == host].set_index("month")["value"]
            rel = (h / others.reindex(h.index)).rename("value").reset_index()  # the model takes logs: log(host) - log(rest)
            rel = rel.assign(region_id=host, region_name=d[d["region_id"] == host]["region_name"].iat[0],
                             series=series, is_host=True)
            e = gp.event_study(rel, ev, series)
            k0 = e[(e["k"] == 0) & e["estimated"]]
            if len(k0):
                r = k0.iloc[0]
                rows.append({**base, "check_id": "host_vs_rest", "check": "Host relative to the rest of the country",
                             "metric": series, "model": "event study k=0", "coef": r["coef"], "se": r["se"],
                             "ci_low": r["ci_low"], "ci_high": r["ci_high"], "pct_effect": r["pct_effect"],
                             "n_obs": r["n_months"], "region": host,
                             "note": ("Outcome is log(host) minus log(sum of all other regions); "
                                      "month-of-year effects and trend as in the main model.")})
    # (3) Synthetic control p-value using only placebos that fit about as well as the host.
    if inference is not None and len(inference):
        for (host, series), g in inference.groupby(["region_id", "series"]):
            hrow = g[g["is_host"]]
            if hrow.empty:
                continue
            hr = hrow.iloc[0]
            keep = g[~g["is_host"] & (g["rmspe_pre"] <= GOOD_FIT_MULTIPLE * hr["rmspe_pre"])]
            ratios = np.r_[hr["rmspe_ratio"], keep["rmspe_ratio"].to_numpy()]
            rows.append({**base, "check_id": "scm_good_fit_placebos",
                         "check": f"Synthetic control p-value, placebos with pre-entry fit within {GOOD_FIT_MULTIPLE:g}x the host's",
                         "metric": series, "model": "synthetic control", "coef": hr["mean_post_gap_pct"],
                         "p_value": float((ratios >= hr["rmspe_ratio"]).mean()), "n_obs": int(len(ratios)), "region": host,
                         "note": "Placebos kept: " + (", ".join(keep["unit"]) or "none") + "."})
    return rows


def run_robustness(eff: pd.DataFrame | None, cs: pd.DataFrame, balance: pd.DataFrame,
                   tourism: pd.DataFrame, events: pd.DataFrame, inference: pd.DataFrame | None,
                   wild: bool = True) -> pd.DataFrame:
    rows = cost_cap_checks(balance, cs, eff, wild)
    if eff is not None and len(eff):
        rows = moneyball_checks(eff, cs, wild) + rows
    rows += grand_prix_checks(tourism, events, inference)
    out = pd.DataFrame(rows)
    cols = ["study", "check_id", "check", "metric", "model", "coef", "se", "ci_low", "ci_high", "p_value", "p_wild",
            "pct_effect", "r2", "n_obs", "n_teams", "baseline_coef", "dropped", "region", "note"]
    for c in cols:
        if c not in out:
            out[c] = None
    return out[cols]
