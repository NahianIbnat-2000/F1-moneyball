"""Jolpica-F1 ingestion.

Two halves, kept apart on purpose:
  * download_*  : talk to the API, save raw pages untouched to data/raw/jolpica/<season>/
  * parse_*     : pure functions turning raw pages into tidy DataFrames (unit-tested offline)

Finished seasons are cached: if every raw page for a season already exists, no request is made.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from datetime import date
from pathlib import Path

import pandas as pd

from f1moneyball.utils import config
from f1moneyball.utils.http import RateLimitedClient

log = logging.getLogger(__name__)

ENDPOINTS = {
    "results": "results",
    "qualifying": "qualifying",
    "constructor_standings": "constructorStandings",
    "driver_standings": "driverStandings",
}


# --------------------------------------------------------------------------- download
def raw_dir(season: int, root: Path | None = None) -> Path:
    return (root or config.RAW_DIR) / "jolpica" / str(season)


def _is_complete(folder: Path, kind: str) -> bool:
    marker = folder / f"{kind}.complete"
    return marker.exists()


def download_season(
    season: int,
    client: RateLimitedClient,
    kinds: Iterable[str] = ENDPOINTS,
    root: Path | None = None,
    force: bool = False,
) -> list[Path]:
    """Download all pages for each endpoint of one season. Returns written files."""
    cfg = config.sources()["jolpica"]
    base, limit = cfg["base_url"], cfg["page_size"]
    folder = raw_dir(season, root)
    folder.mkdir(parents=True, exist_ok=True)
    current = season >= date.today().year
    written: list[Path] = []
    for kind in kinds:
        if not force and not current and _is_complete(folder, kind):
            log.info("Cached: %s %s", season, kind)
            continue
        offset, total = 0, None
        while total is None or offset < total:
            url = f"{base}/{season}/{ENDPOINTS[kind]}.json"
            payload = client.get_json(url, params={"limit": limit, "offset": offset})
            total = int(payload["MRData"]["total"])
            path = folder / f"{kind}_{offset:05d}.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            written.append(path)
            offset += limit
            if total == 0:
                break
        # A season still in progress is never marked complete.
        if not current:
            (folder / f"{kind}.complete").write_text(str(total), encoding="utf-8")
    return written


PIT_STOPS_FROM = 2011  # the source has pit stop data from 2011 onwards


def race_rounds(season: int, root: Path | None = None) -> list[int]:
    """Rounds of a season, read from the already-downloaded race results (no extra request)."""
    return sorted({int(r["round"]) for r in _races(load_pages(season, "results", root))})


def _round_on_disk(folder: Path, rnd: int, limit: int) -> bool:
    """True only if every page of the round was saved (a run can stop between pages)."""
    pages = sorted(folder.glob(f"pit_stops_r{rnd:02d}_*.json"))
    if not pages:
        return False
    total = int(json.loads(pages[0].read_text(encoding="utf-8"))["MRData"]["total"])
    return len(pages) >= max(1, -(-total // limit))


def download_pit_stops(season: int, client: RateLimitedClient, root: Path | None = None,
                       force: bool = False) -> list[Path]:
    """Pit stops are only served per race, so this makes one request per round (more if a race has
    over 100 stops). Needs the season's results downloaded first. Finished seasons are cached."""
    if season < PIT_STOPS_FROM:
        return []
    cfg = config.sources()["jolpica"]
    base, limit = cfg["base_url"], cfg["page_size"]
    folder = raw_dir(season, root)
    current = season >= date.today().year
    if not force and not current and _is_complete(folder, "pit_stops"):
        log.info("Cached: %s pit_stops", season)
        return []
    written: list[Path] = []
    for rnd in race_rounds(season, root):
        # A round already on disk is kept, so an interrupted run resumes where it stopped.
        if not force and not current and _round_on_disk(folder, rnd, limit):
            continue
        offset, total = 0, None
        while total is None or offset < total:
            payload = client.get_json(f"{base}/{season}/{rnd}/pitstops.json", params={"limit": limit, "offset": offset})
            total = int(payload["MRData"]["total"])
            path = folder / f"pit_stops_r{rnd:02d}_{offset:05d}.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            written.append(path)
            offset += limit
            if total == 0:
                break
    if not current:
        (folder / "pit_stops.complete").write_text(str(len(race_rounds(season, root))), encoding="utf-8")
    return written


def load_pages(season: int, kind: str, root: Path | None = None) -> list[dict]:
    folder = raw_dir(season, root)
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob(f"{kind}_*.json"))]


# --------------------------------------------------------------------------- parse
def _races(pages: list[dict]) -> Iterable[dict]:
    for page in pages:
        yield from page["MRData"].get("RaceTable", {}).get("Races", [])


def _int(x) -> int | None:
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def _lap_ms(t: str | None) -> float | None:
    """'1:23.456' -> 83456.0 ms. Empty or malformed -> None."""
    if not t:
        return None
    try:
        if ":" in t:
            m, s = t.split(":")
            return (int(m) * 60 + float(s)) * 1000
        return float(t) * 1000
    except ValueError:
        return None


def parse_results(pages: list[dict]) -> pd.DataFrame:
    # Paging can split one race across two pages; rows are simply concatenated.
    rows = []
    for race in _races(pages):
        for r in race.get("Results", []):
            rows.append({
                "season": int(race["season"]), "round": int(race["round"]),
                "race_name": race["raceName"], "date": race["date"],
                "circuit_id": race["Circuit"]["circuitId"],
                "driver_id": r["Driver"]["driverId"],
                "driver_name": f'{r["Driver"].get("givenName", "")} {r["Driver"].get("familyName", "")}'.strip(),
                "constructor_id": r["Constructor"]["constructorId"],
                "grid": _int(r.get("grid")), "position": _int(r.get("position")),
                "position_text": r.get("positionText"), "points": float(r.get("points", 0)),
                "laps": _int(r.get("laps")), "status": r.get("status", ""),
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def parse_qualifying(pages: list[dict]) -> pd.DataFrame:
    rows = []
    for race in _races(pages):
        for q in race.get("QualifyingResults", []):
            times = [_lap_ms(q.get(k)) for k in ("Q1", "Q2", "Q3")]
            valid = [t for t in times if t is not None]
            rows.append({
                "season": int(race["season"]), "round": int(race["round"]),
                "driver_id": q["Driver"]["driverId"],
                "constructor_id": q["Constructor"]["constructorId"],
                "position": _int(q.get("position")),
                "q1_ms": times[0], "q2_ms": times[1], "q3_ms": times[2],
                "best_ms": min(valid) if valid else None,
            })
    return pd.DataFrame(rows)


def parse_constructor_standings(pages: list[dict]) -> pd.DataFrame:
    rows = []
    for page in pages:
        for sl in page["MRData"].get("StandingsTable", {}).get("StandingsLists", []):
            for s in sl.get("ConstructorStandings", []):
                rows.append({
                    "season": int(sl["season"]), "round": _int(sl.get("round")),
                    "constructor_id": s["Constructor"]["constructorId"],
                    "constructor_name": s["Constructor"]["name"],
                    "position": _int(s.get("position")), "points": float(s["points"]),
                    "wins": int(s.get("wins", 0)),
                })
    return pd.DataFrame(rows)


def parse_driver_standings(pages: list[dict]) -> pd.DataFrame:
    rows = []
    for page in pages:
        for sl in page["MRData"].get("StandingsTable", {}).get("StandingsLists", []):
            for s in sl.get("DriverStandings", []):
                cons = s.get("Constructors", [])
                rows.append({
                    "season": int(sl["season"]),
                    "driver_id": s["Driver"]["driverId"],
                    "driver_name": f'{s["Driver"].get("givenName", "")} {s["Driver"].get("familyName", "")}'.strip(),
                    # A driver can race for several teams in a season; we keep the last listed.
                    "constructor_id": cons[-1]["constructorId"] if cons else None,
                    "n_constructors": len(cons),
                    "position": _int(s.get("position")), "points": float(s["points"]),
                    "wins": int(s.get("wins", 0)),
                })
    return pd.DataFrame(rows)


def parse_pit_stops(pages: list[dict]) -> pd.DataFrame:
    """One row per stop. Durations are total pit-lane time as published (entry to exit), in seconds."""
    rows = []
    for race in _races(pages):
        for ps in race.get("PitStops", []):
            ms = _lap_ms(ps.get("duration"))
            rows.append({
                "season": int(race["season"]), "round": int(race["round"]),
                "race_name": race["raceName"], "circuit_id": race["Circuit"]["circuitId"],
                "driver_id": ps["driverId"], "stop": _int(ps.get("stop")), "lap": _int(ps.get("lap")),
                "duration_s": ms / 1000 if ms is not None else None,
            })
    return pd.DataFrame(rows, columns=["season", "round", "race_name", "circuit_id", "driver_id", "stop", "lap",
                                       "duration_s"])


PARSERS = {
    "results": parse_results,
    "qualifying": parse_qualifying,
    "constructor_standings": parse_constructor_standings,
    "driver_standings": parse_driver_standings,
}
