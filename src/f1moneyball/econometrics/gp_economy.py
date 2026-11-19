"""The Grand Prix Economy: does hosting a race raise tourism in the host economy?

Data: monthly official series entered by hand (data/manual/gp_tourism_monthly.csv) and
race dates (data/manual/gp_race_events.csv). Each host economy is analysed separately.

1. Event study (host only): log(value) on month-of-year effects, a linear trend and dummies
   for months k = -2..+2 around each race month. HAC standard errors (3 lags).
   Shows whether race months stand out against the usual seasonal pattern, and whether
   neighbouring months fall (displacement). Without a comparison region it is descriptive.

2. Synthetic control (Abadie, Diamond & Hainmueller 2010) for a race ENTRY (the first race
   in the data window): weights on comparison regions (non-negative, summing to 1) chosen
   to match the host's pre-entry log series. The post-entry gap is the estimate.
   Inference by placebo-in-space: rerun for each comparison region; the p-value is the
   rank of the host's post/pre RMSPE ratio among all units. If pre-entry fit is poor
   (pre RMSPE above `MAX_PRE_RMSPE`), the result is flagged and should not be read as causal.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.optimize import minimize

K_WINDOW = (-2, 2)
MIN_MONTHS_ES = 36
MIN_PRE_MONTHS, MIN_DONORS = 24, 3
MAX_PRE_RMSPE = 0.10  # in log points (about 10%)
ES_NOTE = "Compared with the same calendar month in other years, after a linear trend. Descriptive: no comparison region."
POOR_FIT = "Pre-entry fit is poor: do not read the gap as an effect."
# Months after this are left out of both designs: COVID-19 closures (from March 2020) move tourism far more
# than any race, and no comparison region escaped them. The series stay in the published data.
ANALYSIS_END = pd.Period("2019-12", freq="M")


def _monthly(df: pd.DataFrame, series: str) -> pd.DataFrame:
    d = df[(df["series"] == series)].copy()
    d["month"] = pd.PeriodIndex(d["month"], freq="M")
    d["y"] = np.log(pd.to_numeric(d["value"], errors="coerce"))
    d = d[d["month"] <= ANALYSIS_END]
    return d.dropna(subset=["y"])


def event_study(df: pd.DataFrame, events: pd.DataFrame, series: str = "arrivals") -> pd.DataFrame:
    rows = []
    d = _monthly(df, series)
    for region, g in d[d["is_host"]].groupby("region_id"):
        g = g.sort_values("month").copy()
        race_months = {m for m in (pd.Period(x, freq="M") for x in events[events["region_id"] == region]["race_start_date"])
                       if m <= ANALYSIS_END}
        base = {"region_id": region, "region_name": g["region_name"].iat[0], "series": series}
        if len(g) < MIN_MONTHS_ES or not race_months:
            rows.append({**base, "k": None, "estimated": False,
                         "note": (f"Not estimated: needs {MIN_MONTHS_ES} months and at least one race "
                                  f"(has {len(g)} months, {len(race_months)} races).")})
            continue
        g["moy"] = g["month"].dt.month.astype(str)
        g["trend"] = np.arange(len(g))
        terms = []
        for k in range(K_WINDOW[0], K_WINDOW[1] + 1):
            name = f"k_{'m' if k < 0 else 'p'}{abs(k)}"
            g[name] = g["month"].apply(lambda m, k=k, rm=race_months: int((m - k) in rm))
            terms.append((k, name))
        fit = smf.ols("y ~ trend + C(moy) + " + " + ".join(n for _, n in terms), data=g).fit(
            cov_type="HAC", cov_kwds={"maxlags": 3})
        for k, name in terms:
            lo, hi = fit.conf_int().loc[name]
            rows.append({**base, "k": k, "estimated": True, "coef": float(fit.params[name]), "se": float(fit.bse[name]),
                         "ci_low": float(lo), "ci_high": float(hi), "pct_effect": float(np.expm1(fit.params[name]) * 100),
                         "n_months": int(len(g)), "n_races": len(race_months),
                         "note": ES_NOTE})
    return pd.DataFrame(rows)


def scm_weights(y_treated: np.ndarray, Y_donors: np.ndarray) -> np.ndarray:
    """Non-negative weights summing to 1 minimising pre-period squared error."""
    j = Y_donors.shape[1]
    obj = lambda w: float(np.sum((y_treated - Y_donors @ w) ** 2))  # noqa: E731
    res = minimize(obj, np.full(j, 1 / j), method="SLSQP", bounds=[(0, 1)] * j,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}], options={"maxiter": 500, "ftol": 1e-10})
    w = np.clip(res.x, 0, None)
    return w / w.sum()


def _fit_unit(panel: pd.DataFrame, unit: str, donors: list[str], pre: np.ndarray) -> dict:
    y = panel[unit].to_numpy()
    Y = panel[donors].to_numpy()
    w = scm_weights(y[pre], Y[pre])
    synth = Y @ w
    gap = y - synth
    rmspe_pre = float(np.sqrt(np.mean(gap[pre] ** 2)))
    rmspe_post = float(np.sqrt(np.mean(gap[~pre] ** 2)))
    return {"weights": dict(zip(donors, w, strict=True)), "synth": synth, "gap": gap, "rmspe_pre": rmspe_pre,
            "rmspe_post": rmspe_post, "ratio": rmspe_post / rmspe_pre if rmspe_pre > 0 else np.inf}


def synthetic_control(df: pd.DataFrame, events: pd.DataFrame, series: str = "arrivals") -> tuple[pd.DataFrame, pd.DataFrame]:
    d = _monthly(df, series)
    paths, inference = [], []
    donors_all = sorted(d[~d["is_host"]]["region_id"].unique())
    for host in sorted(d[d["is_host"]]["region_id"].unique()):
        ev = events[events["region_id"] == host]
        entry = pd.Period(min(ev["race_start_date"]), freq="M") if len(ev) else None
        wide = d[d["region_id"].isin([host, *donors_all])].pivot_table(index="month", columns="region_id", values="y").dropna()
        donors = [c for c in donors_all if c in wide.columns]
        base = {"region_id": host, "series": series}
        if entry is None or len(donors) < MIN_DONORS:
            inference.append({**base, "unit": host, "is_host": True, "estimated": False,
                              "note": f"Not estimated: needs a race date and {MIN_DONORS} comparison regions (has {len(donors)})."})
            continue
        pre = (wide.index < entry)
        if pre.sum() < MIN_PRE_MONTHS or (~pre).sum() < 1:
            inference.append({**base, "unit": host, "is_host": True, "estimated": False,
                              "note": f"Not estimated: needs {MIN_PRE_MONTHS} pre-entry months (has {int(pre.sum())})."})
            continue
        pre = np.asarray(pre)
        fit = _fit_unit(wide, host, donors, pre)
        for m, yv, sv, gv, p in zip(wide.index.astype(str), wide[host], fit["synth"], fit["gap"], pre, strict=True):
            paths.append({**base, "month": m, "observed": float(yv), "synthetic": float(sv), "gap": float(gv),
                          "period": "pre-entry" if p else "post-entry"})
        units = [(host, True, fit)]
        for dn in donors:  # placebo in space: each donor treated as if it hosted
            others = [x for x in donors if x != dn]
            units.append((dn, False, _fit_unit(wide, dn, others, pre)))
        ratios = sorted((u[2]["ratio"] for u in units), reverse=True)
        p_value = (ratios.index(fit["ratio"]) + 1) / len(units)
        for unit, is_host, f in units:
            inference.append({**base, "unit": unit, "is_host": is_host, "estimated": True, "entry_month": str(entry),
                              "rmspe_pre": f["rmspe_pre"], "rmspe_post": f["rmspe_post"], "rmspe_ratio": f["ratio"],
                              "mean_post_gap_pct": float(np.expm1(np.mean(f["gap"][~pre])) * 100),
                              "p_value": p_value if is_host else None,
                              "weights": "; ".join(f"{k}: {v:.2f}" for k, v in f["weights"].items() if v >= 0.01) if is_host else None,
                              "poor_pre_fit": bool(f["rmspe_pre"] > MAX_PRE_RMSPE),
                              "note": ("Host. " if is_host else "Placebo (no race). ")
                                      + (POOR_FIT if f["rmspe_pre"] > MAX_PRE_RMSPE else "")})
    return pd.DataFrame(paths), pd.DataFrame(inference)
