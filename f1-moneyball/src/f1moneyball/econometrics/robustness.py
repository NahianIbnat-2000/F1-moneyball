"""Robustness and sensitivity checks for the three studies, collected in one long table.

Every row is one estimate: which study and check it belongs to, the coefficient that matters, its
uncertainty, and a note. `baseline_coef` repeats the main result so a reader can see how much a
check moves it.

Few clusters. The resource models have only eight teams and the dose-response model six. Clustered
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
from scipy import stats

from f1moneyball.econometrics import comparability as comp
from f1moneyball.econometrics import cost_cap as cc
from f1moneyball.econometrics import gp_economy as gp
from f1moneyball.econometrics.inference import WildCluster
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
    b, se, G = float(fit.params[var]), float(fit.bse[var]), int(data["team_id"].nunique())
    # Small-sample alternative to the normal-based clustered p-value: t distribution with G - 1 degrees of
    # freedom (Cameron and Miller 2015). Reported alongside, not instead of, the published p_value.
    p_t = float(2 * stats.t.sf(abs(b / se), G - 1)) if se > 0 and G > 1 else float("nan")
    return {"coef": b, "se": se, "ci_low": float(lo), "ci_high": float(hi),
            "p_value": float(fit.pvalues[var]), "p_t": p_t, "r2": float(fit.rsquared), "n_obs": int(len(data)),
            "n_teams": G}


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
            if wild and spec == "twfe":
                row["ci_boot_low"], row["ci_boot_high"] = WildCluster(f, panel, x, "team_id").ci()
            rows.append(row)
            sub = panel[~panel["season"].isin(RESET_SEASONS)]
            rows.append({**base, "check_id": "no_reset_seasons", "check": "Without rule-reset seasons (2014, 2017, 2022)",
                         "model": spec, **_fit(f, sub, x), "baseline_coef": b["coef"]})
            pos_panel = panel.dropna(subset=["position"])
            pos = _fit(f"position ~ {x}{fe}", pos_panel, x)
            if wild and spec != "pooled":  # same few-cluster correction as the main models
                pos["p_wild"] = wild_cluster_p(f"position ~ {x}{fe}", pos_panel, x, "team_id")
            if wild and spec == "twfe":
                pos["ci_boot_low"], pos["ci_boot_high"] = WildCluster(f"position ~ {x}{fe}", pos_panel, x, "team_id").ci()
            rows.append({**base, "check_id": "position_outcome",
                         "check": "Outcome: championship position (negative = better)", "model": spec,
                         **pos, "baseline_coef": None})
            if spec != "pooled":
                ctrl = panel.dropna(subset=["completion_rate", "mean_grid_to_finish"])
                h4 = _fit(f"points_share ~ {x} + completion_rate + mean_grid_to_finish{fe}", ctrl, x)
                if wild:
                    h4["p_wild"] = wild_cluster_p(f"points_share ~ {x} + completion_rate + mean_grid_to_finish{fe}", ctrl, x, "team_id")
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


# ----------------------------------------------------------------------------- accounting comparability
FLOW_METRICS = ("turnover", "staff_costs")  # amounts that scale with the length of the period; headcount is an average
NORMAL_PERIOD_DAYS = (350, 380)


def account_meta(fin: pd.DataFrame) -> pd.DataFrame:
    """One row per team-season: length of the accounting period in days and whether the accounts are group-consolidated."""
    f = fin[(fin["source_class"] != "missing") & fin["season_mapped"].notna()].copy()
    f["season"] = f["season_mapped"].astype(int)
    f["period_days"] = (pd.to_datetime(f["financial_year_end"]) - pd.to_datetime(f["financial_year_start"])).dt.days + 1
    f["group_accounts"] = f["accounting_basis"].fillna("").str.contains("group").astype(int)
    return f.drop_duplicates(["team_id", "season"])[["team_id", "season", "period_days", "group_accounts"]]


def annualised(eff: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Copy of `eff` with flow amounts scaled to 365 days where the accounting period was not about a year."""
    e = eff.merge(meta[["team_id", "season", "period_days"]], on=["team_id", "season"], how="left")
    lo, hi = NORMAL_PERIOD_DAYS
    odd = e["metric"].isin(FLOW_METRICS) & e["period_days"].notna() & ((e["period_days"] < lo) | (e["period_days"] > hi))
    e.loc[odd, "value"] = e.loc[odd, "value"] * 365 / e.loc[odd, "period_days"]
    return e.drop(columns="period_days")


SBP_RE = r"share-based payments of ([\d,]+) \(£000\)"


def without_share_based_pay(eff: pd.DataFrame, fin: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Copy of `eff` with share-based payments removed from staff costs, where the filing's amount is recorded
    in the notes column (the first amount quoted, which is the figure for that year). Share-based payments are a
    non-cash charge that can swing a lot from year to year."""
    f = fin[(fin["metric"] == "staff_costs") & fin["season_mapped"].notna()].copy()
    f["sbp"] = f["notes"].fillna("").str.extract(SBP_RE, expand=False).str.replace(",", "").astype(float) * 1000
    f = f.dropna(subset=["sbp"])
    f["season"] = f["season_mapped"].astype(int)
    e = eff.merge(f[["team_id", "season", "sbp"]].assign(metric="staff_costs"), on=["team_id", "season", "metric"], how="left")
    hit = e["sbp"].notna()
    e.loc[hit, "value"] = e.loc[hit, "value"] - e.loc[hit, "sbp"]
    return e.drop(columns="sbp"), int(hit.sum())


def comparability_checks(eff: pd.DataFrame, cs: pd.DataFrame, fin: pd.DataFrame, wild: bool = True) -> list[dict]:
    """Do the main within-team results depend on how the accounts were drawn up?

    scope_control: adds an indicator for group-consolidated accounts in the lagged year. Several teams switch
    between company-only and group accounts, which can change reported amounts without any change in spending.
    annualised_periods: flow amounts from periods that are not about twelve months are scaled to 365 days.
    """
    rows: list[dict] = []
    meta = account_meta(fin)
    lag = meta[["team_id", "season", "group_accounts"]].copy()
    lag["season"] += 1
    lag = lag.rename(columns={"group_accounts": "group_lag"})
    eff_a = annualised(eff, meta)
    pos = cs[["team_id", "season", "position"]]
    x = "log_resource_lag"
    for metric in METRICS:
        g = eff[(eff["metric"] == metric) & (eff["value"] > 0)]
        if g.empty:
            continue
        ccy = g["currency"].mode().iat[0]
        base = {"study": "does-money-buy-speed", "metric": metric, "model": "twfe"}
        panel = lagged_panel(eff, metric, ccy).merge(lag, on=["team_id", "season"], how="left").fillna({"group_lag": 0})
        panel = panel.merge(pos, on=["team_id", "season"], how="left")
        if panel["team_id"].nunique() < 4:
            continue
        for outcome, cid, label in (("points_share", "scope_control", "Control for group vs company accounts (lagged year)"),
                                    ("position", "scope_control_position", "Position outcome, control for group vs company accounts")):
            d = panel.dropna(subset=[outcome])
            f0 = f"{outcome} ~ {x} + C(team_id) + C(season)"
            f1 = f"{outcome} ~ {x} + group_lag + C(team_id) + C(season)"
            b0 = _fit(f0, d, x)
            r = _fit(f1, d, x)
            if wild:
                r["p_wild"] = wild_cluster_p(f1, d, x, "team_id")
            r["note"] = (f"{int(d['group_lag'].sum())} team-seasons follow a year of group-consolidated accounts. "
                         "Same sample and fixed effects as the main estimate.")
            rows.append({**base, "check_id": cid, "check": label, **r, "baseline_coef": b0["coef"]})
        if metric in FLOW_METRICS:
            pa = lagged_panel(eff_a, metric, ccy)
            f = f"points_share ~ {x} + C(team_id) + C(season)"
            r = _fit(f, pa, x)
            if wild:
                r["p_wild"] = wild_cluster_p(f, pa, x, "team_id")
            n_odd = int(((meta["period_days"] < NORMAL_PERIOD_DAYS[0]) | (meta["period_days"] > NORMAL_PERIOD_DAYS[1])).sum())
            r["note"] = f"{n_odd} team-season accounts cover more or less than about a year; their amounts are scaled to 365 days."
            rows.append({**base, "check_id": "annualised_periods", "check": "Accounting periods scaled to 12 months",
                         **r, "baseline_coef": _fit(f, lagged_panel(eff, metric, ccy), x)["coef"]})
    eff_s, n_sbp = without_share_based_pay(eff, fin)
    if n_sbp:
        f = f"points_share ~ {x} + C(team_id) + C(season)"
        ps = lagged_panel(eff_s, "staff_costs", "GBP")
        r = _fit(f, ps, x)
        if wild:
            r["p_wild"] = wild_cluster_p(f, ps, x, "team_id")
        r["note"] = (f"Share-based payments removed from {n_sbp} team-season staff-cost figures where the filing amount is "
                     "recorded (McLaren 2023 to 2025). Other teams' filings may include smaller amounts not recorded here.")
        rows.append({"study": "does-money-buy-speed", "metric": "staff_costs", "model": "twfe",
                     "check_id": "staff_costs_ex_share_based_pay", "check": "Staff costs without share-based payments",
                     **r, "baseline_coef": _fit(f, lagged_panel(eff, "staff_costs", "GBP"), x)["coef"]})
    return rows


def comparability_sample_checks(eff: pd.DataFrame, cs: pd.DataFrame, fin: pd.DataFrame, wild: bool = True) -> list[dict]:
    """Two-way models on samples restricted by financial comparability of the lagged resource (see comparability.py).

    Samples: High only; High and Moderate; and the full sample with team-by-accounting-basis fixed effects,
    which gives each team a separate level before and after a switch between group and company accounts.
    """
    cls = comp.classify(fin)[["team_id", "season", "metric", "category"]]
    seg = comp.boundary_segments(fin)
    pos = cs[["team_id", "season", "position"]]
    x, rows = "log_resource_lag", []
    samples = (("sample_high", "Sample: lagged resource of high comparability", {"High"}),
               ("sample_high_moderate", "Sample: lagged resource of high or moderate comparability", {"High", "Moderate"}))
    for metric in METRICS:
        g = eff[(eff["metric"] == metric) & (eff["value"] > 0)]
        if g.empty:
            continue
        panel = lagged_panel(eff, metric, g["currency"].mode().iat[0]).merge(pos, on=["team_id", "season"], how="left")
        lag_cls = cls[cls["metric"] == metric].assign(season=lambda d: d["season"] + 1)[["team_id", "season", "category"]]
        panel = panel.merge(lag_cls, on=["team_id", "season"], how="left")
        panel = panel.merge(seg.assign(season=lambda d: d["season"] + 1), on=["team_id", "season"], how="left")
        panel["segment"] = panel["segment"].fillna(panel["team_id"])
        base_ps = _fit(f"points_share ~ {x} + C(team_id) + C(season)", panel, x)["coef"]
        base_pos = _fit(f"position ~ {x} + C(team_id) + C(season)", panel.dropna(subset=["position"]), x)["coef"]
        variants = [(cid, lab, panel[panel["category"].isin(keep)], " + C(team_id) + C(season)")
                    for cid, lab, keep in samples]
        variants.append(("segment_fe", "Team-by-accounting-basis fixed effects (full sample)", panel,
                         " + C(segment) + C(season)"))
        for cid, lab, sub, fe in variants:
            for outcome, base in (("points_share", base_ps), ("position", base_pos)):
                d = sub.dropna(subset=[outcome])
                G, n_all = d["team_id"].nunique(), len(panel.dropna(subset=[outcome]))
                row = {"study": "does-money-buy-speed", "metric": metric, "check_id": f"{cid}_{outcome}",
                       "check": f"{lab}; outcome: {outcome.replace('_', ' ')}", "model": "twfe", "baseline_coef": base}
                if G < 4 or len(d) < 20:
                    rows.append({**row, "n_obs": len(d), "n_teams": G,
                                 "note": f"Not estimated: {len(d)} team-seasons from {G} teams is too few."})
                    continue
                f = f"{outcome} ~ {x}{fe}"
                r = _fit(f, d, x)
                if wild:
                    r["p_wild"] = wild_cluster_p(f, d, x, "team_id")
                r["note"] = f"{len(d)} of {n_all} team-seasons, {G} of {panel['team_id'].nunique()} teams."
                rows.append({**row, **r})
    return rows


def alternative_outcome_checks(eff: pd.DataFrame, cs: pd.DataFrame, wild: bool = True) -> list[dict]:
    """Two-way models with other outcomes, the reverse direction and a two-season lag.

    * points share among the covered teams only (the main outcome uses all constructors' points);
    * normalised position: (position - 1) / (number of constructors - 1), 0 = champion, 1 = last;
    * reverse direction: this season's log resource on last season's points share;
    * resource lagged two seasons.
    All are associations. They describe timing, they do not identify cause.
    """
    rows, x = [], "log_resource_lag"
    n_con = cs.groupby("season")["team_id"].nunique().rename("n_constructors").reset_index()
    sport = cs[["team_id", "season", "position", "points_share"]].merge(n_con, on="season")
    sport["norm_position"] = (sport["position"] - 1) / (sport["n_constructors"] - 1)
    fe = " + C(team_id) + C(season)"
    for metric in METRICS:
        g = eff[(eff["metric"] == metric) & (eff["value"] > 0)]
        if g.empty:
            continue
        ccy = g["currency"].mode().iat[0]
        panel = lagged_panel(eff, metric, ccy).merge(sport[["team_id", "season", "norm_position"]], on=["team_id", "season"])
        if "points_share_in_group" in eff.columns:
            cov = eff[(eff["metric"] == metric) & (eff["currency"] == ccy)][["team_id", "season", "points_share_in_group"]]
            panel = panel.merge(cov.drop_duplicates(["team_id", "season"]), on=["team_id", "season"], how="left")
        else:
            panel["points_share_in_group"] = np.nan
        base = _fit(f"points_share ~ {x}{fe}", panel, x)["coef"]
        specs = [("outcome_covered_share", "Outcome: points share among covered teams only", "points_share_in_group", base),
                 ("outcome_norm_position", "Outcome: normalised position (0 = champion, 1 = last)", "norm_position", None)]
        for cid, lab, out, b0 in specs:
            d = panel.dropna(subset=[out])
            if d["team_id"].nunique() < 4:
                continue
            f = f"{out} ~ {x}{fe}"
            r = _fit(f, d, x)
            if wild:
                r["p_wild"] = wild_cluster_p(f, d, x, "team_id")
            rows.append({"study": "does-money-buy-speed", "metric": metric, "check_id": cid, "check": lab,
                         "model": "twfe", **r, "baseline_coef": b0})
        # resource lagged two seasons
        lv = g[g["currency"] == ccy][["team_id", "season", "value"]].drop_duplicates(["team_id", "season"])
        lag2 = lv.assign(season=lv["season"] + 2, log_resource_lag2=np.log(lv["value"]))[["team_id", "season", "log_resource_lag2"]]
        d = panel.merge(lag2, on=["team_id", "season"]).dropna(subset=["log_resource_lag2"])
        if d["team_id"].nunique() >= 4:
            f = f"points_share ~ log_resource_lag2{fe}"
            r = _fit(f, d, "log_resource_lag2")
            if wild:
                r["p_wild"] = wild_cluster_p(f, d, "log_resource_lag2", "team_id")
            rows.append({"study": "does-money-buy-speed", "metric": metric, "check_id": "lag_two_seasons",
                         "check": "Resource lagged two seasons", "model": "twfe", **r, "baseline_coef": base})
        # reverse direction: does last season's points share go with this season's resource?
        rev = lv.assign(log_resource=np.log(lv["value"])).merge(
            sport[["team_id", "season", "points_share"]].assign(season=lambda s: s["season"] + 1)
            .rename(columns={"points_share": "points_share_lag"}), on=["team_id", "season"])
        if rev["team_id"].nunique() >= 4:
            f = f"log_resource ~ points_share_lag{fe}"
            r = _fit(f, rev, "points_share_lag")
            if wild:
                r["p_wild"] = wild_cluster_p(f, rev, "points_share_lag", "team_id")
            r["note"] = ("Coefficient: change in log resource for a points share one unit (100 percentage points) "
                         "higher last season; multiply by 0.01 for one percentage point.")
            rows.append({"study": "does-money-buy-speed", "metric": metric, "check_id": "reverse_direction",
                         "check": "Reverse direction: log resource on last season's points share", "model": "twfe",
                         **r, "baseline_coef": None})
    return rows


def real_terms_checks(eff: pd.DataFrame, cpi: pd.DataFrame, wild: bool = True) -> list[dict]:
    """Money measures in constant prices, deflated by the UK CPI annual index (ONS series D7BT).

    Only the pooled and team-FE models can change: with season fixed effects, a price index that is the same for
    every team in a season is absorbed by the season effect, so the two-way estimate is identical by construction.
    """
    rows: list[dict] = []
    if cpi is None or cpi.empty:
        return rows
    idx = cpi.set_index("year")["cpi_index"]
    x = "log_resource_lag"
    for metric in FLOW_METRICS:
        e = eff.copy()
        m = (e["metric"] == metric) & e["season"].isin(idx.index)
        if not m.any():
            continue
        e.loc[m, "value"] = e.loc[m, "value"] / e.loc[m, "season"].map(idx) * 100
        panel = lagged_panel(e, metric, "GBP")
        for spec in ("pooled", "team_fe"):
            f = f"points_share ~ {x}{SPECS[spec]}"
            r = _fit(f, panel, x)
            if wild and spec != "pooled":
                r["p_wild"] = wild_cluster_p(f, panel, x, "team_id")
            # D7BT is defined with 2015 = 100; the base is fixed by ONS, not read from the values (2014 also rounds to 100.0).
            r["note"] = ("Deflated by the UK CPI annual index (ONS D7BT, 2015 = 100), so amounts are in 2015 pounds. "
                         "The two-way model is unchanged by construction, so it is not repeated.")
            rows.append({"study": "does-money-buy-speed", "metric": metric, "model": spec, "check_id": "real_terms",
                         "check": "Money in constant prices (UK CPI)", **r,
                         "baseline_coef": _fit(f, lagged_panel(eff, metric, "GBP"), x)["coef"]})
    return rows


def holm(p: pd.Series) -> pd.Series:
    """Holm step-down adjusted p-values (controls the family-wise error rate)."""
    order = p.sort_values().index
    m, run, out = len(p), 0.0, pd.Series(index=p.index, dtype=float)
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * p[i]))
        out[i] = run
    return out


def multiple_testing_rows(rows: list[dict]) -> list[dict]:
    """Holm adjustment over the main within-team family: three measures x two outcomes, team and season effects,
    using the wild bootstrap p-values. The family was fixed before looking at the adjusted values."""
    fam = [r for r in rows if r.get("study") == "does-money-buy-speed" and r.get("model") == "twfe"
           and r.get("check_id") in ("baseline", "position_outcome") and pd.notna(r.get("p_wild"))]
    if len(fam) < 2:
        return []
    adj = holm(pd.Series([r["p_wild"] for r in fam]))
    out = []
    for r, a in zip(fam, adj, strict=True):
        outcome = "points share" if r["check_id"] == "baseline" else "championship position"
        out.append({"study": r["study"], "check_id": "holm_adjusted", "check": f"Holm-adjusted bootstrap p, {outcome}",
                    "metric": r["metric"], "model": "twfe", "coef": r["coef"], "se": r.get("se"), "p_value": r.get("p_wild"),
                    "p_wild": float(a), "n_obs": r.get("n_obs"), "n_teams": r.get("n_teams"), "baseline_coef": r["coef"],
                    "note": f"Family of {len(fam)} tests (3 measures x 2 outcomes). p_value = unadjusted bootstrap p; "
                            "p_wild = Holm-adjusted."})
    return out


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
        hrows = tourism[tourism["region_id"] == host]
        if hrows.empty:
            continue
        # Only regions in the host's own country are comparable.
        same = tourism[(tourism["country"] == hrows["country"].iat[0]) & (tourism["region_id"] != host)] \
            if "country" in tourism else tourism[tourism["region_id"] != host]
        if same.empty:
            continue
        for series in sorted(hrows["series"].unique()):
            # (1) Same race months, other states: is the race-month rise specific to the host?
            for state, sg in same[same["series"] == series].groupby("region_id"):
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
            others = d[d["region_id"].isin(same["region_id"].unique())].groupby("month")["value"].sum()
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
            if not bool(hr.get("estimated", True)) or pd.isna(hr.get("rmspe_pre")):
                continue  # no synthetic control for this host (e.g. no comparison regions)
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
                   wild: bool = True, fin: pd.DataFrame | None = None, cpi: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = cost_cap_checks(balance, cs, eff, wild)
    if eff is not None and len(eff):
        mb = moneyball_checks(eff, cs, wild)
        if fin is not None and len(fin):
            mb += comparability_checks(eff, cs, fin, wild)
            mb += comparability_sample_checks(eff, cs, fin, wild)
        mb += alternative_outcome_checks(eff, cs, wild)
        mb += real_terms_checks(eff, cpi, wild)
        mb += multiple_testing_rows(mb)
        rows = mb + rows
    rows += grand_prix_checks(tourism, events, inference)
    out = pd.DataFrame(rows)
    cols = ["study", "check_id", "check", "metric", "model", "coef", "se", "ci_low", "ci_high",
            "ci_boot_low", "ci_boot_high", "p_value", "p_t", "p_wild",
            "pct_effect", "r2", "n_obs", "n_teams", "baseline_coef", "dropped", "region", "note"]
    for c in cols:
        if c not in out:
            out[c] = None
    return out[cols]
