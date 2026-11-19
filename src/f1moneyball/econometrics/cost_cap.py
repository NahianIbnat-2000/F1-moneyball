"""The Cost Cap Paradox: did competitive balance change after the 2021 cost cap?

Three designs, each with a stated limit:

1. Interrupted time series (ITS) on season-level balance indicators.
     y_t = a + b*trend + c*post2021 + d*post2021*(t - 2021) [+ e*post2022] + u_t
   Newey-West (HAC) standard errors, 1 lag. Spec B adds a 2022 level dummy for the technical
   reset; the cap's separate level change is then identified from the 2021 season ALONE.
   ITS has no control group: every team was treated, so this is descriptive evidence.

2. Placebo break years inside the pre-cap period (no real policy change). If fake breaks
   often produce level changes as large as the 2021 one, the 2021 change is not unusual.

3. Dose-response comparison (exposure x post) with team and season fixed effects, plus an
   event study by season. Exposure = standardised log of a team's mean pre-cap resources
   (2018-2020, one financial measure, one currency). Teams that spent more had to cut more.
   Even this cannot separate the cap from the 2022 rules if big spenders adapted differently,
   so results are labelled "suggestive".
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

CAP_YEAR, TECH_YEAR, LAST_SEASON = 2021, 2022, 2025
INDICATORS = ["hhi_normalized", "gini", "top3_share", "leader_points_share", "rank_persistence"]
MIN_PRE, MIN_POST = 6, 3
EXPOSURE_YEARS = (2018, 2020)
EVENT_WINDOW = (2014, LAST_SEASON)
REFERENCE = 2020
MIN_EXPOSED_TEAMS = 4


def _ci(fit, name):
    lo, hi = fit.conf_int().loc[name]
    return float(lo), float(hi)


def _its_row(d: pd.DataFrame, y: str, break_year: int, spec: str, kind: str) -> dict:
    d = d.copy()
    d["trend"] = d["season"] - d["season"].min()
    d["post"] = (d["season"] >= break_year).astype(int)
    d["post_trend"] = d["post"] * (d["season"] - break_year)
    formula = f"{y} ~ trend + post + post_trend"
    if spec == "B":
        d["post_tech"] = (d["season"] >= TECH_YEAR).astype(int)
        formula += " + post_tech"
    fit = smf.ols(formula, data=d).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
    lo, hi = _ci(fit, "post")
    row = {"kind": kind, "indicator": y, "break_year": break_year, "specification": spec, "formula": formula,
           "estimated": True, "n_seasons": int(len(d)), "n_pre": int((d["post"] == 0).sum()),
           "n_post": int(d["post"].sum()), "level_change": float(fit.params["post"]), "se": float(fit.bse["post"]),
           "ci_low": lo, "ci_high": hi, "p_value": float(fit.pvalues["post"]),
           "slope_change": float(fit.params["post_trend"]), "r2": float(fit.rsquared), "se_type": "Newey-West, 1 lag"}
    if spec == "B":
        row["tech_level_change"] = float(fit.params["post_tech"])
    return row


def its_models(balance: pd.DataFrame) -> pd.DataFrame:
    b = balance[balance["season"] <= LAST_SEASON].sort_values("season")
    rows = []
    for y in INDICATORS:
        d = b[["season", y]].dropna()
        n_pre, n_post = int((d["season"] < CAP_YEAR).sum()), int((d["season"] >= CAP_YEAR).sum())
        if n_pre < MIN_PRE or n_post < MIN_POST:
            rows.append({"kind": "its", "indicator": y, "break_year": CAP_YEAR, "specification": "A",
                         "estimated": False, "n_seasons": len(d), "n_pre": n_pre, "n_post": n_post,
                         "note": f"Not estimated: needs {MIN_PRE} seasons before 2021 and {MIN_POST} from 2021."})
            continue
        a = _its_row(d, y, CAP_YEAR, "A", "its")
        a["note"] = "Level and slope change at 2021. No control group: descriptive, not causal."
        bb = _its_row(d, y, CAP_YEAR, "B", "its")
        bb["note"] = ("Adds a 2022 dummy for the technical reset. The 2021 level change is then identified "
                      "from the 2021 season alone, so treat it with great caution.")
        rows += [a, bb]
        # Placebos: fake breaks using pre-cap seasons only, each with at least 3 seasons after.
        pre = d[d["season"] < CAP_YEAR]
        for fake in range(int(pre["season"].min()) + 3, CAP_YEAR - 2):
            r = _its_row(pre, y, fake, "A", "placebo")
            r["note"] = "Placebo: no policy change at this break year."
            rows.append(r)
    out = pd.DataFrame(rows)
    # Share of placebo level changes at least as large (in absolute value) as the actual one.
    for y in INDICATORS:
        actual = out[(out["indicator"] == y) & (out["kind"] == "its") & (out["specification"] == "A") & out["estimated"]]
        plac = out[(out["indicator"] == y) & (out["kind"] == "placebo")]
        if len(actual) and len(plac):
            share = float((plac["level_change"].abs() >= abs(actual["level_change"].iat[0])).mean())
            out.loc[actual.index, "placebo_share_as_large"] = share
            out.loc[actual.index, "n_placebos"] = len(plac)
    return out


def exposure_panel(cs: pd.DataFrame, eff: pd.DataFrame | None) -> tuple[pd.DataFrame, dict]:
    """Team exposure from pre-cap resources, joined to team-seasons in the event window."""
    info = {"metric": None, "currency": None, "n_teams": 0}
    if eff is None or eff.empty:
        return pd.DataFrame(), info
    usable = eff[(eff["value"] > 0) & ~eff["exclusion_reason"].fillna("").str.startswith("More than one")]
    pre = usable[usable["season"].between(*EXPOSURE_YEARS)]
    if pre.empty:
        return pd.DataFrame(), info
    metric = pre["metric"].mode().iat[0]
    currency = pre[pre["metric"] == metric]["currency"].mode().iat[0]
    p = pre[(pre["metric"] == metric) & (pre["currency"] == currency)]
    expo = np.log(p.groupby("team_id")["value"].mean())
    expo = (expo - expo.mean()) / expo.std(ddof=0) if len(expo) > 1 and expo.std(ddof=0) > 0 else expo * 0
    info = {"metric": metric, "currency": currency, "n_teams": int(len(expo))}
    panel = cs[cs["season"].between(*EVENT_WINDOW) & cs["team_id"].isin(expo.index)][["team_id", "season", "points_share"]].copy()
    panel["exposure"] = panel["team_id"].map(expo)
    panel["post"] = (panel["season"] >= CAP_YEAR).astype(int)
    return panel, info


def dose_response(cs: pd.DataFrame, eff: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel, info = exposure_panel(cs, eff)
    base = {"kind": "dose_response", "indicator": "points_share", "break_year": CAP_YEAR,
            "specification": "Exposure x post, team and season fixed effects",
            "exposure_measure": f"{info['metric']} ({info['currency']}), mean {EXPOSURE_YEARS[0]}-{EXPOSURE_YEARS[1]}"}
    if info["n_teams"] < MIN_EXPOSED_TEAMS or panel.empty:
        row = {**base, "estimated": False, "n_teams": info["n_teams"],
               "note": f"Not estimated: needs pre-cap financial figures ({EXPOSURE_YEARS[0]}-{EXPOSURE_YEARS[1]}) "
                       f"for at least {MIN_EXPOSED_TEAMS} teams in one measure and currency (has {info['n_teams']})."}
        return pd.DataFrame([row]), pd.DataFrame()
    groups = panel["team_id"].astype("category").cat.codes
    fit = smf.ols("points_share ~ exposure:post + C(team_id) + C(season)", data=panel).fit(
        cov_type="cluster", cov_kwds={"groups": groups})
    k = "exposure:post"
    lo, hi = _ci(fit, k)
    row = {**base, "estimated": True, "n_obs": int(len(panel)), "n_teams": info["n_teams"],
           "n_seasons": int(panel["season"].nunique()), "level_change": float(fit.params[k]), "se": float(fit.bse[k]),
           "ci_low": lo, "ci_high": hi, "p_value": float(fit.pvalues[k]), "r2": float(fit.rsquared),
           "se_type": "clustered by team",
           "note": ("Change in points share after 2021 per one standard deviation more pre-cap resources. "
                    "Suggestive only: cannot separate the cap from the 2022 technical rules."
                    + (f" Only {info['n_teams']} clusters." if info["n_teams"] < 10 else ""))}
    # Event study: exposure x season, reference season 2020.
    ev = panel.copy()
    seasons = sorted(ev["season"].unique())
    terms = []
    for s in seasons:
        if s == REFERENCE:
            continue
        ev[f"e{s}"] = ev["exposure"] * (ev["season"] == s)
        terms.append(f"e{s}")
    efit = smf.ols(f"points_share ~ {' + '.join(terms)} + C(team_id) + C(season)", data=ev).fit(
        cov_type="cluster", cov_kwds={"groups": groups})
    es = []
    for s in seasons:
        if s == REFERENCE:
            es.append({"season": int(s), "coef": 0.0, "se": 0.0, "ci_low": 0.0, "ci_high": 0.0, "is_reference": True})
            continue
        lo, hi = _ci(efit, f"e{s}")
        es.append({"season": int(s), "coef": float(efit.params[f"e{s}"]), "se": float(efit.bse[f"e{s}"]),
                   "ci_low": lo, "ci_high": hi, "is_reference": False})
    es = pd.DataFrame(es)
    es["period"] = np.where(es["season"] < CAP_YEAR, "pre-cap", "cost cap")
    es["n_teams"] = info["n_teams"]
    es["exposure_measure"] = base["exposure_measure"]
    return pd.DataFrame([row]), es


def run_cost_cap(balance: pd.DataFrame, cs: pd.DataFrame, eff: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    its = its_models(balance)
    did, es = dose_response(cs, eff)
    return pd.concat([its, did], ignore_index=True), es
