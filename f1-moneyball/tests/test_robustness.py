"""Robustness checks. SYNTHETIC TEST DATA ONLY."""
import numpy as np
import pandas as pd

from f1moneyball.econometrics.robustness import _cluster_t, wild_cluster_p
from f1moneyball.publishing import publish


def _panel(effect, seed=1, teams=6, seasons=12):
    rng = np.random.default_rng(seed)
    rows = []
    for t in range(teams):
        level = rng.normal()
        for s in range(seasons):
            x = level + rng.normal(scale=0.5)
            rows.append({"team_id": f"t{t}", "season": 2010 + s, "x": x, "y": effect * x + level + rng.normal(scale=0.3)})
    return pd.DataFrame(rows)


def test_cluster_t_matches_statsmodels():
    import statsmodels.formula.api as smf
    d = _panel(0.5)
    fit = smf.ols("y ~ x", d).fit(cov_type="cluster", cov_kwds={"groups": d["team_id"].astype("category").cat.codes})
    X = np.column_stack([np.ones(len(d)), d["x"]])
    b, t = _cluster_t(X, d["y"].to_numpy(), d["team_id"].to_numpy(), 1)
    assert np.isclose(b, fit.params["x"]) and np.isclose(t, fit.tvalues["x"], rtol=1e-6)


def test_wild_bootstrap_rejects_real_effect_and_not_null():
    strong = wild_cluster_p("y ~ x + C(team_id)", _panel(1.0), "x", "team_id", draws=999)
    null = wild_cluster_p("y ~ x + C(team_id)", _panel(0.0, seed=3), "x", "team_id", draws=999)
    assert strong < 0.05 and null > 0.05


def test_robustness_rows_are_publishable(tmp_path):
    from f1moneyball.econometrics.robustness import run_robustness
    d = _panel(0.1)
    cs = pd.DataFrame({"team_id": d["team_id"], "season": d["season"], "points_share": d["y"].rank(pct=True) / 6,
                       "position": d.groupby("season")["y"].rank(ascending=False), "completion_rate": 0.9,
                       "mean_grid_to_finish": d["x"]})
    eff = pd.DataFrame({"team_id": d["team_id"], "season": d["season"], "metric": "turnover", "currency": "GBP",
                        "value": np.exp(d["x"] + 18), "points_share": cs["points_share"], "exclusion_reason": None})
    bal = pd.DataFrame({"season": range(2010, 2026), "hhi_normalized": np.linspace(.1, .2, 16), "gini": .5,
                        "top3_share": .7, "leader_points_share": .3, "rank_persistence": .8})
    r = run_robustness(eff, cs, bal, pd.DataFrame(), pd.DataFrame(), None, wild=False)
    assert {"baseline", "no_reset_seasons", "h3_cap_interaction", "leave_one_team_out", "its_no_2020"} <= set(r["check_id"])
    publish.publish_dataset("robustness_checks", r, out_dir=tmp_path)
