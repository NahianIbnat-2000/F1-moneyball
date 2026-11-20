"""Accounting-comparability checks: annualising, account scope, share-based pay, Holm adjustment, and the
validation warnings that point to them."""
import numpy as np
import pandas as pd
import pytest

from f1moneyball.econometrics.robustness import account_meta, annualised, holm, multiple_testing_rows, without_share_based_pay
from f1moneyball.validation.checks import financial_comparability


def _fin(rows):
    base = {"source_class": "audited", "currency": "GBP", "accounting_basis": "UK GAAP; company only", "notes": ""}
    return pd.DataFrame([{**base, **r} for r in rows])


def test_account_meta_period_and_scope():
    fin = _fin([
        {"team_id": "a", "season_mapped": 2015, "metric": "turnover", "value": 1e8,
         "financial_year_start": "2015-01-01", "financial_year_end": "2015-12-31"},
        {"team_id": "a", "season_mapped": 2016, "metric": "turnover", "value": 1e8,
         "financial_year_start": "2016-01-01", "financial_year_end": "2017-06-30",
         "accounting_basis": "UK GAAP; group consolidated"},
    ])
    m = account_meta(fin).set_index("season")
    assert m.loc[2015, "period_days"] == 365
    assert m.loc[2016, "period_days"] == 547  # inclusive of both dates
    assert m.loc[2015, "group_accounts"] == 0 and m.loc[2016, "group_accounts"] == 1


def test_annualised_scales_flows_not_headcount():
    eff = pd.DataFrame({"team_id": ["a"] * 3, "season": [2016] * 3, "metric": ["turnover", "staff_costs", "headcount"],
                        "value": [150.0, 75.0, 400.0]})
    meta = pd.DataFrame({"team_id": ["a"], "season": [2016], "period_days": [547]})
    out = annualised(eff, meta).set_index("metric")["value"]
    assert out["turnover"] == pytest.approx(150 * 365 / 547)
    assert out["staff_costs"] == pytest.approx(75 * 365 / 547)
    assert out["headcount"] == 400.0  # an average over the period, not a total


def test_annualised_leaves_normal_years_alone():
    eff = pd.DataFrame({"team_id": ["a"], "season": [2015], "metric": ["turnover"], "value": [100.0]})
    meta = pd.DataFrame({"team_id": ["a"], "season": [2015], "period_days": [366]})
    assert annualised(eff, meta)["value"].iat[0] == 100.0


def test_share_based_pay_removed_only_where_recorded():
    eff = pd.DataFrame({"team_id": ["m", "m", "r"], "season": [2023, 2024, 2023], "metric": ["staff_costs"] * 3,
                        "value": [134_922_000.0, 179_936_000.0, 100_000_000.0]})
    fin = _fin([
        {"team_id": "m", "season_mapped": 2023, "metric": "staff_costs",
         "notes": "Includes share-based payments of 20,302 (£000). Local copy: x.pdf"},
        {"team_id": "m", "season_mapped": 2024, "metric": "staff_costs",
         "notes": "Includes share-based payments of 57,191 (£000). Restated ... with share-based payments of 38,163."},
        {"team_id": "r", "season_mapped": 2023, "metric": "staff_costs", "notes": "Local copy: y.pdf"},
    ])
    out, n = without_share_based_pay(eff, fin)
    assert n == 2
    v = out.set_index(["team_id", "season"])["value"]
    assert v[("m", 2023)] == 134_922_000 - 20_302_000
    assert v[("m", 2024)] == 179_936_000 - 57_191_000  # first amount quoted is that year's figure
    assert v[("r", 2023)] == 100_000_000


def test_holm_matches_textbook_example():
    p = pd.Series([0.01, 0.04, 0.03, 0.005])
    adj = holm(p)
    # sorted 0.005, 0.01, 0.03, 0.04 -> 0.02, 0.03, 0.06, 0.06 (monotone)
    assert adj.tolist() == pytest.approx([0.03, 0.06, 0.06, 0.02])


def test_multiple_testing_uses_six_test_family():
    rows = []
    for m, pb, pp in (("turnover", 0.15, 0.055), ("staff_costs", 0.042, 0.013), ("headcount", 0.25, 0.046)):
        rows.append({"study": "does-money-buy-speed", "check_id": "baseline", "model": "twfe", "metric": m, "coef": 0.1, "p_wild": pb})
        rows.append({"study": "does-money-buy-speed", "check_id": "position_outcome", "model": "twfe", "metric": m,
                     "coef": -2.0, "p_wild": pp})
        rows.append({"study": "does-money-buy-speed", "check_id": "baseline", "model": "team_fe", "metric": m, "coef": 0.1, "p_wild": 0.5})
    out = multiple_testing_rows(rows)
    assert len(out) == 6
    smallest = min(out, key=lambda r: r["p_value"])
    assert smallest["p_wild"] == pytest.approx(6 * 0.013)
    assert all(r["p_wild"] >= r["p_value"] for r in out)


def test_validation_warns_on_period_scope_and_jumps():
    fin = _fin([
        {"team_id": "a", "season_mapped": 2015, "metric": "turnover", "value": 100.0,
         "financial_year_start": "2015-01-01", "financial_year_end": "2015-12-31"},
        {"team_id": "a", "season_mapped": 2016, "metric": "turnover", "value": 200.0,
         "financial_year_start": "2016-01-01", "financial_year_end": "2017-06-30",
         "accounting_basis": "UK GAAP; group consolidated"},
    ])
    issues = {i.check: i for i in financial_comparability(fin, verified=pd.DataFrame())}
    assert set(issues) == {"period_length", "accounting_scope_switch", "yoy_change"}
    assert all(i.severity == "warning" for i in issues.values())
    assert "547 days" in issues["period_length"].message


def test_verified_change_clears_warning_only_while_values_match():
    fin = _fin([
        {"team_id": "a", "season_mapped": 2015, "metric": "turnover", "value": 100.0,
         "financial_year_start": "2015-01-01", "financial_year_end": "2015-12-31"},
        {"team_id": "a", "season_mapped": 2016, "metric": "turnover", "value": 200.0,
         "financial_year_start": "2016-01-01", "financial_year_end": "2016-12-31"},
    ])
    rec = pd.DataFrame([{"team_id": "a", "metric": "turnover", "season": 2016, "value": 200, "prior_value": 100}])
    assert "yoy_change" not in {i.check for i in financial_comparability(fin, verified=rec)}
    fin.loc[fin.season_mapped == 2016, "value"] = 210.0  # data changed after the check
    assert "yoy_change" in {i.check for i in financial_comparability(fin, verified=rec)}


def test_validation_quiet_on_clean_series():
    fin = _fin([
        {"team_id": "a", "season_mapped": y, "metric": "turnover", "value": 100.0 + y - 2015,
         "financial_year_start": f"{y}-01-01", "financial_year_end": f"{y}-12-31"} for y in (2015, 2016, 2017)
    ])
    assert financial_comparability(fin) == []


def test_no_nan_in_holm():
    assert not np.isnan(holm(pd.Series([0.2, 0.9])).values).any()


def _toy_panel():
    rng = np.random.default_rng(0)
    rows = []
    for t in "abcde":
        for y in range(2012, 2020):
            v = float(np.exp(rng.normal(18, 0.3)))
            rows.append({"team_id": t, "season": y, "metric": "turnover", "value": v, "currency": "GBP",
                         "points_share": float(rng.uniform(0.05, 0.4)), "exclusion_reason": None})
    return pd.DataFrame(rows)


def test_real_terms_skipped_without_index():
    from f1moneyball.econometrics.robustness import real_terms_checks
    assert real_terms_checks(_toy_panel(), None, wild=False) == []


def test_real_terms_cannot_change_two_way_model():
    """A deflator common to all teams in a season is absorbed by season fixed effects."""
    from f1moneyball.econometrics.models import lagged_panel
    from f1moneyball.econometrics.robustness import SPECS, _fit
    eff = _toy_panel()
    cpi = pd.DataFrame({"year": range(2012, 2020), "cpi_index": [90 * 1.03 ** i for i in range(8)]})
    deflated = eff.copy()
    deflated["value"] = deflated["value"] / deflated["season"].map(cpi.set_index("year")["cpi_index"]) * 100
    f = f"points_share ~ log_resource_lag{SPECS['twfe']}"
    a = _fit(f, lagged_panel(eff, "turnover", "GBP"), "log_resource_lag")["coef"]
    b = _fit(f, lagged_panel(deflated, "turnover", "GBP"), "log_resource_lag")["coef"]
    assert a == pytest.approx(b, abs=1e-9)


def test_real_terms_rows_for_pooled_and_team_fe():
    from f1moneyball.econometrics.robustness import real_terms_checks
    cpi = pd.DataFrame({"year": range(2012, 2020), "cpi_index": [90 * 1.03 ** i for i in range(8)]})
    out = real_terms_checks(_toy_panel(), cpi, wild=False)
    assert {r["model"] for r in out} == {"pooled", "team_fe"}
    assert all(r["check_id"] == "real_terms" for r in out)
