"""Tests for efficiency indicators and models. All data here is SYNTHETIC and only for testing."""
import numpy as np
import pandas as pd
import pytest

from f1moneyball.econometrics.efficiency import efficiency_table, financial_panel
from f1moneyball.econometrics.models import run_models
from f1moneyball.publishing import publish
from f1moneyball.publishing import status as st

TEAMS = ["red_bull", "mercedes", "ferrari", "mclaren", "williams", "haas"]


def make_data(seasons=range(2012, 2020), currency="GBP", beta=0.08, seed=1):
    rng = np.random.default_rng(seed)
    fin, cs = [], []
    res = {t: rng.uniform(80e6, 300e6) for t in TEAMS}
    prev = dict(res)
    for s in seasons:
        raw = {}
        for t in TEAMS:
            res[t] = prev[t] * rng.uniform(0.85, 1.2)
            raw[t] = max(0.01, beta * np.log(prev[t] / 1e8) + 0.15 + rng.normal(0, 0.01))
            fin.append(dict(team_id=t, season_mapped=s, entity_name=f"{t} ltd", metric="operating_costs",
                            value=res[t], currency=currency, source_class="audited", confidence="high",
                            financial_year_end=f"{s}-12-31"))
        total = sum(raw.values())
        for i, t in enumerate(sorted(TEAMS, key=lambda x: -raw[x])):
            cs.append(dict(season=s, team_id=t, team_name=t, points=raw[t] * 800, points_share=raw[t] / total,
                           position=i + 1, wins=0, podiums=0, completion_rate=0.9, mechanical_dnf_rate=0.05,
                           mean_grid_to_finish=0.0, median_quali_gap_pct=1.0))
        prev = dict(res)
    return pd.DataFrame(fin), pd.DataFrame(cs)


def test_shares_and_ratio():
    fin, cs = make_data(seasons=[2015])
    eff = efficiency_table(financial_panel(fin, cs), min_teams=4)
    assert eff["included"].all()
    assert eff["resource_share"].sum() == pytest.approx(1)
    assert eff["points_share_in_group"].sum() == pytest.approx(1)
    row = eff.iloc[0]
    assert row["efficiency_ratio"] == pytest.approx(row["points_share_in_group"] / row["resource_share"])
    assert row["points_per_million"] == pytest.approx(row["points"] / (row["value"] / 1e6))


def test_small_and_mixed_currency_groups_are_excluded_with_reason():
    fin, cs = make_data(seasons=[2015])
    fin.loc[fin["team_id"].isin(["haas", "williams", "mclaren"]), "currency"] = "EUR"
    eff = efficiency_table(financial_panel(fin, cs), min_teams=4)
    assert not eff["included"].any()
    assert eff["exclusion_reason"].str.contains("different currency").all()


def test_duplicate_entities_are_excluded():
    fin, cs = make_data(seasons=[2015])
    extra = fin.iloc[[0]].assign(entity_name="second entity")
    eff = efficiency_table(financial_panel(pd.concat([fin, extra]), cs), min_teams=4)
    dup = eff[eff["team_id"] == fin.iloc[0]["team_id"]]
    assert len(dup) == 2 and dup["exclusion_reason"].str.contains("More than one entity").all()


def test_profit_measures_excluded_and_headcount_is_persons():
    fin, cs = make_data(seasons=[2015])
    profit = fin.assign(metric="operating_profit", value=-fin["value"])
    heads = fin.assign(metric="headcount", value=700.0)
    eff = efficiency_table(financial_panel(pd.concat([fin, profit, heads]), cs), min_teams=4)
    assert "operating_profit" not in set(eff["metric"])
    h = eff[eff["metric"] == "headcount"]
    assert (h["currency"] == "persons").all() and h["included"].all()
    assert h["points_per_million"].isna().all()


def test_estimates_flagged_not_reported():
    fin, cs = make_data(seasons=[2015])
    fin.loc[0, "source_class"] = "secondary_estimate"
    panel = financial_panel(fin, cs)
    assert panel["is_reported"].sum() == len(TEAMS) - 1


def test_models_recover_positive_association():
    fin, cs = make_data()
    res = run_models(efficiency_table(financial_panel(fin, cs)))
    pooled = res.set_index("specification").loc["Pooled OLS"]
    assert pooled["estimated"] and pooled["coef"] > 0 and pooled["ci_low"] > 0
    assert set(res["specification"]) == {"Pooled OLS", "Team fixed effects", "Team and season fixed effects"}
    assert pooled["n_teams"] == len(TEAMS) and "clusters" in pooled["note"]
    assert pooled["effect_10pct_pp"] == pytest.approx(pooled["coef"] * np.log(1.1) * 100)


def test_models_refuse_small_samples():
    fin, cs = make_data(seasons=[2015, 2016])
    res = run_models(efficiency_table(financial_panel(fin, cs)))
    assert not res["estimated"].any() and res["note"].str.startswith("Not estimated").all()


def test_outputs_publishable_and_status(tmp_path):
    fin, cs = make_data()
    eff = efficiency_table(financial_panel(fin, cs))
    models = run_models(eff)
    publish.publish_dataset("efficiency", eff, out_dir=tmp_path)
    publish.publish_dataset("model_results", models, out_dir=tmp_path)
    out = st.build_status({"efficiency": eff, "model_results": models}, [], out_dir=tmp_path)
    by = {d["dataset_id"]: d for d in out["datasets"]}
    assert by["efficiency"]["status"] == "published" and by["model_results"]["status"] == "published"
    small = efficiency_table(financial_panel(*make_data(seasons=[2015])), min_teams=10)
    out = st.build_status({"efficiency": small}, [], out_dir=tmp_path)
    assert {d["dataset_id"]: d for d in out["datasets"]}["efficiency"]["status"] == "insufficient_coverage"
