"""The standings snapshot must pass arithmetic checks that a transcription error would break."""
import pandas as pd
import pytest

from f1moneyball.ingestion.snapshot import constructor_season_from_snapshot, load_snapshot
from f1moneyball.standardization.teams import add_team_id

ROUNDS = {2010: 19, 2011: 19, 2012: 20, 2013: 19, 2014: 19, 2015: 19, 2016: 21, 2017: 20, 2018: 21,
          2019: 21, 2020: 17, 2021: 22, 2022: 22, 2023: 22, 2024: 24, 2025: 24}
# Seasons where the season's total points follow from the points system alone:
# 2010-2018: 25-18-15-12-10-8-6-4-2-1 = 101 per race (2014: final race double points);
# 2025: no fastest-lap point, plus 6 sprints at 8+7+...+1 = 36.
DETERMINISTIC_TOTAL = {s: 101 * ROUNDS[s] for s in (2010, 2011, 2012, 2013, 2015, 2016, 2017, 2018)}
DETERMINISTIC_TOTAL[2014] = 101 * 18 + 202
DETERMINISTIC_TOTAL[2025] = 101 * 24 + 6 * 36


@pytest.fixture(scope="module")
def snap():
    return load_snapshot()


def test_rounds_and_wins(snap):
    for s, g in snap.groupby("season"):
        assert g["round"].iat[0] == ROUNDS[s]
        assert g["wins"].sum() == ROUNDS[s], s


def test_positions_and_order(snap):
    for s, g in snap.groupby("season"):
        g = g.sort_values("position")
        assert list(g["position"]) == list(range(1, len(g) + 1)), s
        assert g["points"].is_monotonic_decreasing, s


@pytest.mark.parametrize("season,total", sorted(DETERMINISTIC_TOTAL.items()))
def test_points_system_totals(snap, season, total):
    assert snap.loc[snap["season"] == season, "points"].sum() == total


def test_known_deduction_2020(snap):
    # 17 races x 102 points minus Racing Point's 15-point deduction (2020 brake-duct ruling).
    assert snap.loc[snap["season"] == 2020, "points"].sum() == 17 * 102 - 15


def test_all_constructors_mapped_and_shares(snap):
    assert add_team_id(snap)["team_id"].notna().all()
    cs = constructor_season_from_snapshot(snap)
    assert cs.groupby("season")["points_share"].sum().round(9).eq(1).all()
    assert not cs.duplicated(["season", "team_id"]).any()
    assert pd.Series(cs["data_source"]).str.contains("snapshot").all()
