import json

import numpy as np
import pandas as pd
import pytest

from f1moneyball.feature_engineering import competitive_balance as cb
from f1moneyball.feature_engineering.sporting import constructor_season, enrich_results
from f1moneyball.ingestion import jolpica
from f1moneyball.publishing import publish
from f1moneyball.standardization.teams import add_team_id, classify_status, constructor_to_team
from f1moneyball.utils import config
from f1moneyball.utils.http import RateLimitedClient, SourceUnavailable
from f1moneyball.validation import checks


# ---------------------------------------------------------------- parsing
def test_parse_results_handles_split_pages(results_pages):
    df = jolpica.parse_results(results_pages)
    assert len(df) == 20
    assert df.groupby("round").size().tolist() == [10, 10]
    assert df["points"].dtype == float


def test_parse_qualifying_lap_times(qualifying_pages):
    q = jolpica.parse_qualifying(qualifying_pages)
    first = q.iloc[0]
    assert first["q1_ms"] == pytest.approx(90_000.0)
    assert first["q2_ms"] is None or np.isnan(first["q2_ms"])
    assert first["best_ms"] == pytest.approx(80_000.0)


def test_lap_time_parser_edge_cases():
    assert jolpica._lap_ms("1:23.456") == pytest.approx(83_456)
    assert jolpica._lap_ms("") is None
    assert jolpica._lap_ms("DNF") is None


# ---------------------------------------------------------------- standardization
def test_team_mapping_is_one_to_one_and_covers_rebrands():
    m = constructor_to_team()
    assert m["force_india"] == m["racing_point"] == m["aston_martin"] == "silverstone"
    assert m["toro_rosso"] == m["alphatauri"] == m["rb"] == "faenza"
    assert m["renault"] == m["lotus_f1"] == m["alpine"] == "enstone"


def test_unknown_constructor_is_flagged():
    df = add_team_id(pd.DataFrame({"constructor_id": ["mclaren", "brand_new_team"], "season": [2099, 2099]}))
    issues = checks.mapped_teams(df, "x")
    assert issues and issues[0].severity == "error" and "brand_new_team" in issues[0].message


@pytest.mark.parametrize("status,expected", [
    ("Finished", "finished"), ("+1 Lap", "finished"), ("Lapped", "finished"), ("Engine", "mechanical"),
    ("Collision", "incident"), ("Retired", "unspecified"), ("Disqualified", "disqualified"),
    ("Did not start", "not_started"), ("Something odd", "other"),
])
def test_classify_status(status, expected):
    assert classify_status(status) == expected


# ---------------------------------------------------------------- balance metrics
def test_balance_metrics_equal_shares():
    pts = [10, 10, 10, 10]
    assert cb.hhi(pts) == pytest.approx(0.25)
    assert cb.hhi_normalized(pts) == pytest.approx(0.0)
    assert cb.gini(pts) == pytest.approx(0.0)
    assert cb.coefficient_of_variation(pts) == pytest.approx(0.0)


def test_balance_metrics_monopoly():
    pts = [100, 0, 0, 0]
    assert cb.hhi(pts) == pytest.approx(1.0)
    assert cb.hhi_normalized(pts) == pytest.approx(1.0)
    assert cb.gini(pts) == pytest.approx(0.75)  # max Gini for n=4 is (n-1)/n
    assert cb.top_k_share(pts, 3) == pytest.approx(1.0)


def test_shares_reject_zero_total():
    with pytest.raises(ValueError):
        cb.shares([0, 0])


# ---------------------------------------------------------------- feature tables
@pytest.fixture
def tables(results_pages, qualifying_pages, standings_pages):
    r = add_team_id(jolpica.parse_results(results_pages))
    q = add_team_id(jolpica.parse_qualifying(qualifying_pages))
    s = add_team_id(jolpica.parse_constructor_standings(standings_pages))
    return r, q, s


def test_constructor_season(tables):
    r, q, s = tables
    cs = constructor_season(s, r, q)
    assert len(cs) == 5
    assert cs["points_share"].sum() == pytest.approx(1.0)
    rb = cs.set_index("team_id").loc["red_bull"]
    assert rb["podiums"] == 4  # both cars finished P1 and P2 in both races
    alpine = cs.set_index("team_id").loc["enstone"]
    assert alpine["mechanical_dnfs"] == 1
    assert alpine["completion_rate"] == pytest.approx(2 / 4)  # both cars retired in race 2
    assert cs.set_index("team_id").loc["red_bull", "poles"] == 2


def test_grid_to_finish(tables):
    r, _, _ = tables
    e = enrich_results(r)
    race1_winner = e[(e["round"] == 1) & (e["position"] == 1)].iloc[0]
    assert race1_winner["grid_to_finish"] == 9  # started 10th, won
    retired = e[e["status"] == "Engine"].iloc[0]
    assert np.isnan(retired["grid_to_finish"])


def test_balance_table_rank_persistence(tables):
    r, q, s = tables
    cs = constructor_season(s, r, q)
    cs2 = cs.copy()
    cs2["season"] = 2100
    bt = cb.balance_table(pd.concat([cs, cs2]))
    assert len(bt) == 2
    assert bt.iloc[1]["rank_persistence"] == pytest.approx(1.0)
    assert bt.iloc[1]["mean_abs_rank_change"] == 0


# ---------------------------------------------------------------- validation
def test_position_checks_catch_impossible_values(tables):
    r, _, _ = tables
    bad = r.copy()
    bad.loc[0, "position"] = 99
    bad.loc[1, "position"] = bad.loc[2, "position"]
    names = {i.check for i in checks.finishing_positions(bad)}
    assert {"positions_le_field", "positions_unique"} <= names


def _fin_row(**kw):
    row = dict(team_id="mclaren", season_mapped=2022, entity_name="McLaren Racing Limited",
               entity_registration="00000000", metric="revenue", value=100_000_000, currency="GBP",
               financial_year_start="2022-01-01", financial_year_end="2022-12-31",
               accounting_basis="FRS 102", source_class="audited", source_name="Companies House",
               source_url="https://example.org/filing", document_title="Annual report 2022", document_page="12",
               publication_date="2023-09-30",
               retrieval_date="2026-11-19", confidence="high", entered_by="test", notes="",
               transformation="none", comparability_warning="")
    row.update(kw)
    return row


def test_financial_validation_good_row_passes():
    df = pd.DataFrame([_fin_row()])
    assert [i for i in checks.financial_observations(df, {"mclaren"}) if i.severity == "error"] == []


def test_financial_validation_catches_problems():
    df = pd.DataFrame([
        _fin_row(source_url=""),                                           # no provenance
        _fin_row(metric="turnover", currency="pounds"),                    # bad currency
        _fin_row(metric="staff_costs", value=5e9),                         # implausible
        _fin_row(metric="operating_profit", financial_year_end="2021-06-30"),  # end before start
        _fin_row(metric="headcount", source_class="rumour"),               # bad enum
        _fin_row(metric="estimated_budget", source_class="secondary_estimate", confidence="low"),  # no warning
        _fin_row(metric="staff_costs", document_title=""),                  # no document
    ])
    names = {i.check for i in checks.financial_observations(df, {"mclaren"})}
    assert {"provenance", "currency_iso", "plausible_range", "date_sequence", "enum:source_class",
            "comparability_warning", "provenance:document_title"} <= names


def test_empty_financial_table_is_warning_not_error():
    issues = checks.financial_observations(pd.DataFrame(), {"mclaren"})
    assert issues[0].severity == "warning"


def test_seed_files_validate():
    reg = pd.read_csv(config.MANUAL_DIR / "regulation_events.csv")
    assert [i for i in checks.regulation_events(reg) if i.severity == "error"] == []
    fin = pd.read_csv(config.MANUAL_DIR / "financial_observations.csv")
    team_ids = set(config.team_mapping()["lineages"])
    assert [i for i in checks.financial_observations(fin, team_ids) if i.severity == "error"] == []


# ---------------------------------------------------------------- http client
class FakeResp:
    def __init__(self, status, body=None):
        self.status_code, self._body, self.url = status, body or {}, "https://x"
        self.content = json.dumps(self._body).encode()

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), 0

    def get(self, *a, **k):
        self.calls += 1
        return self.responses.pop(0)


def test_client_retries_then_succeeds(tmp_path):
    sleeps = []
    s = FakeSession([FakeResp(503), FakeResp(200, {"ok": 1})])
    c = RateLimitedClient(session=s, sleep=sleeps.append, clock=lambda: 0.0,
                          retrieval_log=tmp_path / "log.jsonl")
    assert c.get_json("https://x") == {"ok": 1}
    assert s.calls == 2 and any(x >= 2 for x in sleeps)
    entry = json.loads((tmp_path / "log.jsonl").read_text())
    assert entry["status"] == 200 and len(entry["sha256"]) == 64


def test_client_gives_up_and_raises():
    s = FakeSession([FakeResp(503)] * 3)
    c = RateLimitedClient(session=s, sleep=lambda x: None, max_retries=3)
    with pytest.raises(SourceUnavailable):
        c.get_json("https://x")


def test_client_hard_fails_on_404():
    c = RateLimitedClient(session=FakeSession([FakeResp(404)]), sleep=lambda x: None)
    with pytest.raises(SourceUnavailable):
        c.get_json("https://x")


def test_download_paginates_and_caches(tmp_path, results_pages):
    class Client:
        calls = 0

        def get_json(self, url, params):
            Client.calls += 1
            return results_pages[params["offset"] // 100] if params["offset"] < 200 else results_pages[0]

    # Two pages of 100 each when total = 150
    for p in results_pages:
        p["MRData"]["total"] = "150"
    jolpica.download_season(2015, Client(), kinds=["results"], root=tmp_path)
    assert Client.calls == 2
    jolpica.download_season(2015, Client(), kinds=["results"], root=tmp_path)
    assert Client.calls == 2, "finished season must be served from cache"
    assert len(jolpica.load_pages(2015, "results", root=tmp_path)) == 2


# ---------------------------------------------------------------- publishing
def test_publish_refuses_undocumented_columns(tmp_path):
    df = pd.DataFrame({"season": [2099], "mystery": [1]})
    with pytest.raises(ValueError, match="mystery"):
        publish.publish_dataset("competitive_balance", df, out_dir=tmp_path)


def test_publish_and_manifest(tmp_path, tables):
    r, q, s = tables
    bt = cb.balance_table(constructor_season(s, r, q))
    entry = publish.publish_dataset("competitive_balance", bt, out_dir=tmp_path)
    path = publish.write_manifest([entry], {"n_errors": 0}, out_dir=tmp_path)
    m = json.loads(path.read_text())
    assert m["datasets"]["competitive_balance"]["rows"] == 1
    assert m["is_synthetic_demo"] is False
    data = json.loads((tmp_path / "competitive_balance.json").read_text())
    assert data["columns"][0] == "season"


# ---------------------------------------------------------------- dataset status
from f1moneyball.publishing import status as st  # noqa: E402


def test_registry_is_consistent():
    reg = st.registry()
    dicts = publish.dictionaries()
    srcs = config.sources()
    assert set(dicts) <= set(reg), "every documented dataset must be in config/datasets.yaml"
    for ds_id, spec in reg.items():
        assert spec["status_if_absent"] in st.STATUSES
        assert all(s in srcs for s in spec["source_ids"]), ds_id
        for k in ("would_contain", "why_unavailable", "needed_for_publication"):
            assert spec[k].strip(), (ds_id, k)


def test_status_absent_dataset(tmp_path):
    out = st.build_status({}, [], out_dir=tmp_path)
    by = {d["dataset_id"]: d for d in out["datasets"]}
    assert by["constructor_season"]["status"] == "not_yet_collected"
    assert by["constructor_season"]["observation_count"] == 0
    assert by["constructor_season"]["last_updated"] is None


def test_status_financial_insufficient_coverage(tmp_path):
    fin = pd.DataFrame([_fin_row()])
    out = st.build_status({"financial_observation": fin}, [], out_dir=tmp_path)
    rec = {d["dataset_id"]: d for d in out["datasets"]}["financial_observation"]
    assert rec["status"] == "insufficient_coverage" and "4" in rec["status_note"]
    assert rec["observation_count"] == 1


def test_status_last_updated_only_changes_with_content(tmp_path, tables):
    r, q, s = tables
    bt = cb.balance_table(constructor_season(s, r, q))
    first = st.build_status({"competitive_balance": bt}, [], out_dir=tmp_path)
    second = st.build_status({"competitive_balance": bt}, [], out_dir=tmp_path)
    get = lambda o: {d["dataset_id"]: d for d in o["datasets"]}["competitive_balance"]  # noqa: E731
    assert get(first)["last_updated"] == get(second)["last_updated"]
    assert get(first)["status"] == "published" and get(first)["coverage_start"] == 2099


def test_every_built_column_is_documented(tmp_path, tables):
    r, q, s = tables
    cs = constructor_season(s, r, q)
    publish.publish_dataset("constructor_season", cs, out_dir=tmp_path)
    publish.publish_dataset("race_result", enrich_results(r), out_dir=tmp_path)
    publish.publish_dataset("competitive_balance", cb.balance_table(cs), out_dir=tmp_path)
    entry = publish.publish_dataset("financial_observation", pd.DataFrame([_fin_row()]), out_dir=tmp_path)
    assert entry["columns"]["value"]["missing_treatment"].startswith("Blank only")
    assert entry["limitations"]


# ---------------------------------------------------------------- changelog
from f1moneyball.publishing import changelog as clog  # noqa: E402


def test_changelog_auto_entries_only_on_version_change(tmp_path):
    rec = {"dataset_id": "x", "dataset_name": "X", "version": "v1", "observation_count": 3}
    assert clog.record_dataset_changes({}, [rec], log_dir=tmp_path)[0]["category"] == "new_data"
    assert clog.record_dataset_changes({"x": rec}, [rec], log_dir=tmp_path) == []
    upd = clog.record_dataset_changes({"x": rec}, [{**rec, "version": "v2"}], log_dir=tmp_path)
    assert upd[0]["category"] == "updated_data" and "previously v1" in upd[0]["detail"]
    entries = clog.build_changelog(out_dir=tmp_path, log_dir=tmp_path)
    assert sum(e["automatic"] for e in entries) == 2 and any(not e["automatic"] for e in entries)


def test_changelog_rejects_unknown_category(tmp_path):
    bad = tmp_path / "c.yaml"
    bad.write_text("- {date: 2026-01-01, category: finding, title: t, detail: d}\n")
    with pytest.raises(ValueError):
        clog.build_changelog(out_dir=tmp_path, log_dir=tmp_path, manual=bad)


def test_manifest_records_environment(tmp_path):
    m = json.loads(publish.write_manifest([], {}, out_dir=tmp_path).read_text())
    assert m["environment"]["packages"]["pandas"] and m["environment"]["python"]
