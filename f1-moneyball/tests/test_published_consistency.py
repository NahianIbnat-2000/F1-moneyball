"""Research regression tests: published results, the website and the hub must agree with the approved reference.

The reference (data/metadata/reference_results.json) holds the approved headline results. If a pipeline change moves
a published number, these tests fail until the change is reviewed and the reference is updated on purpose.
"""
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "website" / "public" / "data"
REF = json.loads((ROOT / "data" / "metadata" / "reference_results.json").read_text())
pytestmark = pytest.mark.skipif(not (DATA / "robustness_checks.csv").exists(), reason="no published data")


def _rob():
    return pd.read_csv(DATA / "robustness_checks.csv")


@pytest.mark.parametrize("row", REF["main"], ids=lambda r: f"{r['metric']}-{r['check_id']}")
def test_main_results_match_reference(row):
    r = _rob()
    x = r[(r.check_id == row["check_id"]) & (r.metric == row["metric"]) & (r.model == row["model"])]
    assert len(x) == 1
    x = x.iloc[0]
    assert abs(x.coef - row["coef"]) <= REF["tolerance"]["coef"] * max(1, abs(row["coef"]))
    assert abs(x.p_wild - row["p_wild"]) <= REF["tolerance"]["p"]
    assert int(x.n_obs) == row["n_obs"] and int(x.n_teams) == row["n_teams"]


def test_pooled_and_holm_match_reference():
    m = pd.read_csv(DATA / "model_results.csv").set_index("model_id")
    assert abs(m.loc["turnover_pooled", "coef"] - REF["pooled_turnover_coef"]) <= REF["tolerance"]["coef"]
    h = _rob().query("check_id == 'holm_adjusted'")
    assert len(h) == 6 and abs(h.p_wild.min() - REF["holm_min"]) <= REF["tolerance"]["p"]
    assert (h.p_wild > 0.05).all(), "a within-team result now survives Holm: the paper's conclusions must be reviewed"


def test_bootstrap_ci_agrees_with_bootstrap_p():
    """Where both exist, the test-inversion interval excludes zero exactly when the bootstrap p-value is below 0.05."""
    r = _rob()
    if not {"ci_boot_low", "ci_boot_high"} <= set(r.columns):
        pytest.skip("bootstrap intervals not published yet")
    r = r.dropna(subset=["ci_boot_low", "ci_boot_high", "p_wild"])
    if r.empty:
        pytest.skip("bootstrap intervals not published yet")
    excludes_zero = (r.ci_boot_low > 0) | (r.ci_boot_high < 0)
    assert (excludes_zero == (r.p_wild < 0.05)).all()


def test_website_and_hub_quote_current_numbers():
    rob = _rob()
    staff = rob.query("check_id == 'baseline' and metric == 'staff_costs' and model == 'twfe'").iloc[0]
    pos = rob.query("check_id == 'position_outcome' and metric == 'staff_costs' and model == 'twfe'").iloc[0]
    places = abs(pos.coef) * math.log(1.1)
    articles = (ROOT / "website" / "src" / "lib" / "articles.ts").read_text()
    hub = (ROOT / "website" / "public" / "hub" / "index.html").read_text()
    assert f"{staff.coef:.3f}" in articles
    assert f"about {places:.2f} places" in articles
    assert f"about {places:.1f} places" in hub
    eff = pd.read_csv(DATA / "efficiency.csv")
    turn = eff[(eff.metric == "turnover") & eff.included.astype(bool)] if "included" in eff else eff[eff.metric == "turnover"]
    corr = turn.resource_share.corr(turn.points_share)
    assert f"correlation {corr:.2f}" in hub
    assert not re.search(r"1\.8 percentage points more points share", hub), "hub quotes the superseded headline"


def test_sample_sizes_consistent_across_outputs():
    m = pd.read_csv(DATA / "model_results.csv")
    est = m[m.get("estimated", True).astype(bool)] if "estimated" in m else m
    assert set(est.n_obs) == {r["n_obs"] for r in REF["main"]}
    assert set(est.n_teams) == {r["n_teams"] for r in REF["main"]}
    assert np.isfinite(est.coef).all()
