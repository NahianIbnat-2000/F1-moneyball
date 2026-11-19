"""Cost cap and Grand Prix Economy methods. All data here is SYNTHETIC with known effects."""
import numpy as np
import pandas as pd
import pytest

from f1moneyball.econometrics import cost_cap as cc
from f1moneyball.econometrics import gp_economy as gp
from f1moneyball.publishing import publish
from f1moneyball.validation import checks


# ---------------------------------------------------------------- cost cap
def balance(drop=-0.08, seed=0):
    rng = np.random.default_rng(seed)
    s = np.arange(2010, 2026)
    base = 0.30 + 0.002 * (s - 2010) + rng.normal(0, 0.005, len(s))
    y = base + np.where(s >= 2021, drop, 0)
    df = pd.DataFrame({"season": s})
    for k in cc.INDICATORS:
        df[k] = y
    return df


def test_its_detects_known_level_drop_and_runs_placebos():
    out = cc.its_models(balance(drop=-0.08))
    a = out[(out["kind"] == "its") & (out["specification"] == "A") & (out["indicator"] == "gini")].iloc[0]
    assert a["level_change"] == pytest.approx(-0.08, abs=0.02) and a["ci_high"] < 0
    assert a["n_pre"] == 11 and a["n_post"] == 5
    plac = out[(out["kind"] == "placebo") & (out["indicator"] == "gini")]
    assert len(plac) == a["n_placebos"] > 0
    assert a["placebo_share_as_large"] == 0  # a real 0.08 drop is larger than any placebo
    b = out[(out["kind"] == "its") & (out["specification"] == "B") & (out["indicator"] == "gini")].iloc[0]
    assert "2021 season alone" in b["note"]


def test_its_refuses_short_series():
    out = cc.its_models(balance()[lambda d: d["season"] >= 2018])
    assert not out["estimated"].any() and out["note"].str.startswith("Not estimated").all()


def make_panel(effect=-0.05, seed=2):
    rng = np.random.default_rng(seed)
    teams = [f"t{i}" for i in range(8)]
    spend = {t: 1e8 * (1 + i * 0.4) for i, t in enumerate(teams)}
    expo = np.log(pd.Series(spend))
    expo = (expo - expo.mean()) / expo.std(ddof=0)
    cs, fin = [], []
    for s in range(2014, 2026):
        for t in teams:
            ps = 0.125 + 0.03 * expo[t] + (effect * expo[t] if s >= 2021 else 0) + rng.normal(0, 0.005)
            cs.append({"team_id": t, "season": s, "points_share": ps})
            if 2018 <= s <= 2020:
                fin.append({"team_id": t, "season": s, "metric": "operating_costs", "currency": "GBP",
                            "value": spend[t] * rng.uniform(0.95, 1.05), "exclusion_reason": None})
    return pd.DataFrame(cs), pd.DataFrame(fin)


def test_dose_response_recovers_effect_and_flat_pretrends():
    cs, eff = make_panel(effect=-0.05)
    did, es = cc.dose_response(cs, eff)
    r = did.iloc[0]
    assert r["estimated"] and r["level_change"] == pytest.approx(-0.05, abs=0.01) and r["n_teams"] == 8
    assert "Suggestive" in r["note"]
    pre = es[(es["season"] < 2020)]
    assert pre["coef"].abs().max() < 0.02  # no pre-trend by construction
    assert es.loc[es["season"] == 2020, "is_reference"].iat[0]
    assert es[es["season"] >= 2021]["coef"].mean() == pytest.approx(-0.05, abs=0.015)


def test_dose_response_needs_financials():
    cs, _ = make_panel()
    did, es = cc.dose_response(cs, None)
    assert not did.iloc[0]["estimated"] and es.empty


# ---------------------------------------------------------------- grand prix economy
def tourism(bump=0.15, seed=4, entry="2008-09"):
    rng = np.random.default_rng(seed)
    months = pd.period_range("2004-01", "2015-12", freq="M")
    season = np.sin(2 * np.pi * months.month / 12) * 0.1
    donors = {f"d{i}": 10 + i * 0.3 + season + 0.002 * np.arange(len(months)) + rng.normal(0, 0.01, len(months)) for i in range(5)}
    host = 0.5 * donors["d1"] + 0.5 * donors["d3"] + rng.normal(0, 0.005, len(months))
    race_m = [m for m in months if m.month == 9 and m >= pd.Period(entry, freq="M")]
    host = host + np.array([bump if m in race_m else 0 for m in months])
    rows = []
    for rid, series in [("host", host), *donors.items()]:
        for m, v in zip(months, series, strict=True):
            rows.append({"region_id": rid, "region_name": rid, "is_host": rid == "host", "month": str(m), "series": "arrivals",
                         "value": float(np.exp(v)), "unit": "persons", "source_url": "x", "table_id": "t"})
    events = pd.DataFrame({"region_id": "host", "year": [m.year for m in race_m],
                           "race_start_date": [f"{m.year}-09-20" for m in race_m]})
    return pd.DataFrame(rows), events


def test_event_study_finds_race_month_bump():
    t, e = tourism(bump=0.15)
    es = gp.event_study(t, e).set_index("k")
    assert es.loc[0, "coef"] == pytest.approx(0.15, abs=0.04) and es.loc[0, "ci_low"] > 0
    assert abs(es.loc[-2, "coef"]) < 0.05


def test_synthetic_control_weights_fit_and_inference():
    t, e = tourism(bump=0.15)
    path, inf = gp.synthetic_control(t, e)
    host = inf[inf["is_host"]].iloc[0]
    assert host["rmspe_pre"] < 0.05 and not host["poor_pre_fit"]
    assert "d1" in host["weights"] and "d3" in host["weights"]
    assert host["p_value"] == pytest.approx(1 / 6)  # host ranks first of 6 units
    assert set(path["period"]) == {"pre-entry", "post-entry"}


def test_scm_weights_are_a_simplex():
    rng = np.random.default_rng(0)
    Y = rng.normal(size=(40, 4))
    y = Y @ np.array([0.2, 0.0, 0.8, 0.0])
    w = gp.scm_weights(y, Y)
    assert w.sum() == pytest.approx(1) and (w >= 0).all() and w[2] == pytest.approx(0.8, abs=0.02)


def test_gp_validation():
    t, e = tourism()
    assert [i for i in checks.gp_tourism(t) if i.severity == "error"] == []
    bad = t.copy()
    bad.loc[0, "month"] = "2004/01"
    bad.loc[1, "series"] = "vibes"
    names = {i.check for i in checks.gp_tourism(bad)}
    assert {"month_format", "enum:series"} <= names
    e2 = e.copy()
    e2["race_end_date"] = "2000-01-01"
    e2["source_url"] = "x"
    assert "date_sequence" in {i.check for i in checks.gp_events(e2, t)}


def test_new_outputs_are_documented(tmp_path):
    out = cc.its_models(balance())
    cs, eff = make_panel()
    did, es = cc.dose_response(cs, eff)
    publish.publish_dataset("cost_cap_models", pd.concat([out, did]), out_dir=tmp_path)
    publish.publish_dataset("cost_cap_event_study", es, out_dir=tmp_path)
    t, e = tourism()
    publish.publish_dataset("gp_event_study", gp.event_study(t, e), out_dir=tmp_path)
    path, inf = gp.synthetic_control(t, e)
    publish.publish_dataset("gp_scm_path", path, out_dir=tmp_path)
    publish.publish_dataset("gp_scm_inference", inf, out_dir=tmp_path)
