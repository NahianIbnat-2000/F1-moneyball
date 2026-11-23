"""Financial comparability classification and restricted-sample checks."""
import pandas as pd

from f1moneyball.econometrics import comparability as comp


def _row(team, season, metric="turnover", basis="UK GAAP; company only", start=None, end=None,
         warn=None, notes="", value=100.0):
    return {"team_id": team, "season_mapped": season, "metric": metric, "value": value,
            "accounting_basis": basis, "financial_year_start": start or f"{season}-01-01",
            "financial_year_end": end or f"{season}-12-31", "comparability_warning": warn, "notes": notes,
            "document_title": f"Accounts {season}", "document_page": "p. 10", "source_url": "https://example.org"}


def test_clean_series_is_high():
    c = comp.classify(pd.DataFrame([_row("a", 2015), _row("a", 2016)]))
    assert (c["category"] == "High").all()


def test_boundary_change_is_limited_and_only_in_the_switch_year():
    fin = pd.DataFrame([_row("a", 2015), _row("a", 2016, basis="UK GAAP; group consolidated"),
                        _row("a", 2017, basis="UK GAAP; group consolidated")])
    c = comp.classify(fin).set_index("season")["category"].astype(str)
    assert c.to_dict() == {2015: "High", 2016: "Limited", 2017: "High"}


def test_period_partial_team_sbp_and_missing():
    fin = pd.DataFrame([
        _row("a", 2015, start="2015-01-01", end="2016-06-30"),                       # 547 days
        _row("b", 2015, warn="The racing licence was held by a Malaysian company"),
        _row("c", 2015, metric="staff_costs", notes="Includes share-based payments of 1,000 (£000)."),
        _row("c", 2015, metric="turnover", notes="Includes share-based payments of 1,000 (£000)."),
        _row("d", 2015, value=float("nan")),
        _row("e", 2015, start="2014-09-01", end="2015-08-31"),                       # August year end
    ])
    c = comp.classify(fin).set_index(["team_id", "metric"])["category"].astype(str)
    assert c[("a", "turnover")] == "Limited"
    assert c[("b", "turnover")] == "Limited"
    assert c[("c", "staff_costs")] == "Limited"   # share-based pay matters for staff costs only
    assert c[("c", "turnover")] == "High"
    assert c[("d", "turnover")] == "Insufficient information"
    assert c[("e", "turnover")] == "Moderate"


def test_every_classification_has_reason_and_source():
    fin = pd.read_csv("data/manual/financial_observations.csv")
    c = comp.classify(fin)
    assert c["reasons"].str.len().gt(0).all() and c["source"].str.len().gt(0).all()
    assert set(c["category"].astype(str)) <= set(comp.ORDER)


def test_segments_split_at_basis_change():
    fin = pd.DataFrame([_row("a", 2015), _row("a", 2016, basis="UK GAAP; group consolidated"), _row("a", 2017)])
    seg = comp.boundary_segments(fin)
    assert seg["segment"].nunique() == 3


def test_test_inversion_matches_bootstrap_p_and_brackets_estimate():
    """The vectorised bootstrap reproduces the published p-value at beta0 = 0, and the CI contains the estimate."""
    import numpy as np

    from f1moneyball.econometrics.inference import WildCluster
    from f1moneyball.econometrics.robustness import wild_cluster_p

    rng = np.random.default_rng(1)
    d = pd.DataFrame({"team_id": np.repeat(list("abcdefgh"), 10), "season": np.tile(range(10), 8)})
    d["x"] = rng.normal(size=len(d))
    d["y"] = 0.3 * d["x"] + rng.normal(size=len(d))
    f = "y ~ x + C(team_id) + C(season)"
    w = WildCluster(f, d, "x", "team_id", draws=999)
    assert w.p_value(0.0) == wild_cluster_p(f, d, "x", "team_id", draws=999)
    lo, hi = w.ci()
    assert lo < w.beta < hi
    assert w.p_value(lo - 0.05) < 0.05 and w.p_value(hi + 0.05) < 0.05


def test_constant_weight_draw_counts_as_tie():
    """A draw with the same weight for every cluster reproduces |t| exactly and must count as at least as extreme."""
    import numpy as np
    import pandas as pd

    from f1moneyball.econometrics.inference import WEBB, WildCluster, at_least_as_extreme
    rng = np.random.default_rng(1)
    d = pd.DataFrame({"team_id": np.repeat(list("abcdef"), 8), "x": rng.normal(size=48)})
    d["y"] = 0.3 * d.x + rng.normal(size=48)
    w = WildCluster("y ~ x + C(team_id)", d, "x", "team_id", draws=50, seed=3)
    for c in WEBB:                      # every constant weight vector
        w.W = np.full((1, len(w.G)), c)
        y0 = w.y
        fit = w.Pr @ y0
        _, ts = w._t((fit[:, None] + (y0 - fit)[:, None] * w.W[:, w.idx].T), 0.0)
        assert at_least_as_extreme(ts, w.beta / w.se).all()
