"""Pit stops: download (offline, with a fake client), parsing, flags and within-race gaps.

SYNTHETIC TEST DATA ONLY: the pages copy the shape of Jolpica-F1 responses.
"""
import json

import pandas as pd
import pytest

from f1moneyball.feature_engineering.sporting import pit_season, pit_stop_table
from f1moneyball.ingestion import jolpica
from f1moneyball.publishing import publish
from f1moneyball.validation import checks

TEAMS = {"d1": "red_bull", "d2": "red_bull", "d3": "mercedes", "d4": "mercedes", "d5": "ferrari", "d6": "ferrari"}


def _pit_page(season, rnd, stops, total=None, offset=0):
    race = {"season": str(season), "round": str(rnd), "raceName": f"Test GP {rnd}", "date": f"{season}-04-0{rnd}",
            "Circuit": {"circuitId": f"circuit_{rnd}"},
            "PitStops": [{"driverId": d, "stop": str(s), "lap": str(lap), "time": "14:00:00", "duration": dur}
                         for d, s, lap, dur in stops]}
    return {"MRData": {"total": str(total if total is not None else len(stops)), "offset": str(offset),
                       "RaceTable": {"Races": [race]}}}


def _results(season, rounds):
    return pd.DataFrame([{"season": season, "round": r, "driver_id": d, "constructor_id": t, "team_id": t}
                         for r in rounds for d, t in TEAMS.items()])


def test_parse_pit_stops_reads_seconds_and_minutes():
    df = jolpica.parse_pit_stops([_pit_page(2015, 1, [("d1", 1, 12, "22.5"), ("d3", 1, 14, "1:05.250")])])
    assert list(df["duration_s"]) == pytest.approx([22.5, 65.25])
    assert df["stop"].tolist() == [1, 1] and df["lap"].tolist() == [12, 14]


def test_parse_handles_empty_race():
    df = jolpica.parse_pit_stops([{"MRData": {"total": "0", "RaceTable": {"Races": []}}}])
    assert df.empty and "duration_s" in df.columns


def test_long_stops_flagged_and_gaps_within_race():
    stops = jolpica.parse_pit_stops([_pit_page(2015, 1, [
        ("d1", 1, 10, "21.0"), ("d2", 1, 11, "23.0"),   # red bull median 22.0
        ("d3", 1, 12, "24.0"), ("d4", 1, 13, "24.0"),   # mercedes median 24.0
        ("d5", 1, 14, "25.0"), ("d6", 1, 15, "45:10.0"),  # ferrari: one red-flag wait (excluded)
    ])])
    pits = pit_stop_table(stops, _results(2015, [1]))
    assert pits.loc[pits["driver_id"] == "d6", "is_long_stop"].item()
    gap = pits.drop_duplicates("team_id").set_index("team_id")["gap_to_best_team_s"]
    assert gap["red_bull"] == 0 and gap["mercedes"] == pytest.approx(2.0) and gap["ferrari"] == pytest.approx(3.0)
    season = pit_season(pits).set_index("team_id")
    assert season.loc["ferrari", "service_pit_stops"] == 1
    assert season.loc["mercedes", "median_pit_gap_s"] == pytest.approx(2.0)


def test_race_with_too_few_teams_gets_no_gap():
    stops = jolpica.parse_pit_stops([_pit_page(2015, 1, [("d1", 1, 10, "21.0"), ("d3", 1, 12, "24.0")])])
    pits = pit_stop_table(stops, _results(2015, [1]))
    assert pits["gap_to_best_team_s"].isna().all()


def test_validation_and_publish(tmp_path):
    stops = jolpica.parse_pit_stops([_pit_page(2015, 1, [("d1", 1, 10, "21.0"), ("d3", 1, 12, "24.0"),
                                                         ("d5", 1, 14, "25.0"), ("x9", 1, 3, "-1")])])
    pits = pit_stop_table(stops, _results(2015, [1]))
    found = {i.check: i.severity for i in checks.pit_stops(pits)}
    assert found == {"duration_positive": "error", "team_match": "warning"}
    publish.publish_dataset("pit_stop", pits, out_dir=tmp_path)
    assert json.loads((tmp_path / "pit_stop.json").read_text())["rows"]


class FakeClient:
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def get_json(self, url, params=None):
        self.calls.append((url, params["offset"]))
        rnd = int(url.rstrip("/").split("/")[-2])
        return self.pages[(rnd, params["offset"])]


def _write_results(folder, season, rounds):
    folder.mkdir(parents=True, exist_ok=True)
    races = [{"season": str(season), "round": str(r), "raceName": "x", "date": f"{season}-01-01",
              "Circuit": {"circuitId": "c"}, "Results": []} for r in rounds]
    (folder / "results_00000.json").write_text(json.dumps({"MRData": {"total": "0", "RaceTable": {"Races": races}}}))


def test_download_pages_resumes_and_caches(tmp_path):
    season = 2015
    _write_results(jolpica.raw_dir(season, tmp_path), season, [1, 2])
    many = [("d1", s, s, "22.0") for s in range(1, 131)]
    pages = {(1, 0): _pit_page(season, 1, many[:100], total=130), (1, 100): _pit_page(season, 1, many[100:], total=130, offset=100),
             (2, 0): _pit_page(season, 2, many[:5])}
    # Round 1 already on disk from an interrupted run: only round 2 is requested.
    folder = jolpica.raw_dir(season, tmp_path)
    (folder / "pit_stops_r01_00000.json").write_text(json.dumps(pages[(1, 0)]))
    (folder / "pit_stops_r01_00100.json").write_text(json.dumps(pages[(1, 100)]))
    client = FakeClient(pages)
    jolpica.download_pit_stops(season, client, root=tmp_path)
    assert [c[1] for c in client.calls] == [0] and client.calls[0][0].endswith("/2015/2/pitstops.json")
    assert len(jolpica.parse_pit_stops(jolpica.load_pages(season, "pit_stops", tmp_path))) == 135
    # Season now marked complete: no further requests.
    client2 = FakeClient(pages)
    jolpica.download_pit_stops(season, client2, root=tmp_path)
    assert client2.calls == []


def test_paging_fetches_all_pages(tmp_path):
    season = 2016
    _write_results(jolpica.raw_dir(season, tmp_path), season, [1])
    many = [("d1", s, s, "22.0") for s in range(1, 131)]
    pages = {(1, 0): _pit_page(season, 1, many[:100], total=130), (1, 100): _pit_page(season, 1, many[100:], total=130, offset=100)}
    client = FakeClient(pages)
    jolpica.download_pit_stops(season, client, root=tmp_path)
    assert [c[1] for c in client.calls] == [0, 100]


def test_half_downloaded_round_is_fetched_again(tmp_path):
    season = 2017
    _write_results(jolpica.raw_dir(season, tmp_path), season, [1])
    many = [("d1", s, s, "22.0") for s in range(1, 131)]
    pages = {(1, 0): _pit_page(season, 1, many[:100], total=130), (1, 100): _pit_page(season, 1, many[100:], total=130, offset=100)}
    (jolpica.raw_dir(season, tmp_path) / "pit_stops_r01_00000.json").write_text(json.dumps(pages[(1, 0)]))
    client = FakeClient(pages)
    jolpica.download_pit_stops(season, client, root=tmp_path)
    assert [c[1] for c in client.calls] == [0, 100]


def test_no_requests_before_2011(tmp_path):
    client = FakeClient({})
    assert jolpica.download_pit_stops(2010, client, root=tmp_path) == [] and client.calls == []
