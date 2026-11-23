"""Test fixtures.

SYNTHETIC TEST DATA ONLY. These pages copy the *shape* of Jolpica-F1 responses so parsers
can be tested offline. Points and positions are made up and are never published.
"""
from __future__ import annotations

import pytest

TEAMS = [("red_bull", "Red Bull"), ("mercedes", "Mercedes"), ("ferrari", "Ferrari"),
         ("mclaren", "McLaren"), ("alpine", "Alpine")]
POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


def _driver(i):
    return {"driverId": f"driver_{i}", "givenName": "Test", "familyName": f"Driver{i}"}


def _race(season, rnd, statuses=None):
    statuses = statuses or {}
    results = []
    for i in range(10):
        cid, cname = TEAMS[i // 2]
        st = statuses.get(i, "Finished")
        finished = st == "Finished"
        results.append({
            "position": str(i + 1), "positionText": str(i + 1) if finished else "R",
            "points": str(POINTS[i] if finished else 0), "Driver": _driver(i),
            "Constructor": {"constructorId": cid, "name": cname},
            "grid": str(10 - i if rnd == 1 else i + 1), "laps": "50", "status": st,
        })
    return {"season": str(season), "round": str(rnd), "raceName": f"Test GP {rnd}",
            "date": f"{season}-03-{10 + rnd:02d}", "Circuit": {"circuitId": f"circuit_{rnd}"},
            "Results": results}


def _page(races, total, key="Races", table="RaceTable"):
    return {"MRData": {"total": str(total), table: {key: races}}}


@pytest.fixture
def results_pages():
    r1 = _race(2099, 1)
    r2 = _race(2099, 2, statuses={8: "Engine", 9: "Collision"})
    # Simulate paging that splits race 2 across two pages.
    r2a = dict(r2, Results=r2["Results"][:6])
    r2b = dict(r2, Results=r2["Results"][6:])
    return [_page([r1, r2a], 20), _page([r2b], 20)]


@pytest.fixture
def qualifying_pages():
    races = []
    for rnd in (1, 2):
        q = []
        for i in range(10):
            cid, cname = TEAMS[i // 2]
            q.append({"position": str(i + 1), "Driver": _driver(i),
                      "Constructor": {"constructorId": cid, "name": cname},
                      "Q1": f"1:3{i // 2}.{i}00", "Q2": "", "Q3": f"1:2{i}.000" if i < 5 else ""})
        races.append({"season": "2099", "round": str(rnd), "raceName": "x", "date": "2099-01-01",
                      "Circuit": {"circuitId": "c"}, "QualifyingResults": q})
    return [_page(races, 20)]


@pytest.fixture
def standings_pages():
    totals = [(25 + 18) * 2, (15 + 12) * 2, (10 + 8) * 2, (6 + 4) * 2, (2 + 1) + 0]
    rows = [{"position": str(i + 1), "positionText": str(i + 1), "points": str(p), "wins": str(2 if i == 0 else 0),
             "Constructor": {"constructorId": TEAMS[i][0], "name": TEAMS[i][1]}} for i, p in enumerate(totals)]
    return [{"MRData": {"total": "5", "StandingsTable": {"StandingsLists": [
        {"season": "2099", "round": "2", "ConstructorStandings": rows}]}}}]
