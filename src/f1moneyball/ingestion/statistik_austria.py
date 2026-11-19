"""Build the Austria Grand Prix inputs from Statistik Austria open data and race results.

Inputs (downloaded by hand, kept unchanged in data/source_documents/statistik_austria/):
  OGD_touextsai_Tour_UA_1.csv          monthly arrivals (F-ANK) and overnight stays (F-UEB)
                                        by federal state (C-W96-0) and accommodation type (C-BBTR-0)
  OGD_touextsai_Tour_UA_1_C-W96-0.csv  federal state codes
Race dates come from the published race_result table (race day = Sunday).

Outputs (overwritten):
  data/manual/gp_tourism_monthly.csv   one row per state, month and series (2008-2025)
  data/manual/gp_race_events.csv       one row per year with an F1 race at the Red Bull Ring

Values are summed over all accommodation types. The sum for 2025 equals the national total
Statistik Austria publishes (157,291,806 overnight stays), which is checked below.

Run:  python -m f1moneyball.ingestion.statistik_austria
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from f1moneyball.utils import config

SRC = config.ROOT / "data" / "source_documents" / "statistik_austria"
DATASET = "OGD_touextsai_Tour_UA_1"
META_URL = f"https://data.statistik.gv.at/web/meta.jsp?dataset={DATASET}"
FIRST, LAST = 2008, 2025
HOST = "at_styria"
CIRCUIT = "red_bull_ring"
RETRIEVED = "2026-11-19"
CHECK_2025_STAYS = 157_291_806  # national total published by Statistik Austria for 2025

REGION_ID = {"W96-1": "at_burgenland", "W96-2": "at_carinthia", "W96-3": "at_lower_austria",
             "W96-4": "at_upper_austria", "W96-5": "at_salzburg", "W96-6": "at_styria",
             "W96-7": "at_tyrol", "W96-8": "at_vorarlberg", "W96-9": "at_vienna"}
SERIES = {"F-ANK": ("arrivals", "arrivals"), "F-UEB": ("overnight_stays", "overnight stays")}

HOST_NOTE = ("Host: Red Bull Ring, Spielberg. F1 returned in June 2014 (also raced here 1997-2003). "
             "MotoGP has raced here every August since 2016. 2020: two races without spectators. "
             "Sum over all accommodation types.")
DONOR_NOTE = ("Comparison region, chosen before estimation: every other Austrian federal state, same "
              "statistics office and definitions, no F1 race 2008-2025. The synthetic control sets the weights. "
              "Sum over all accommodation types.")


def build_tourism() -> pd.DataFrame:
    raw = pd.read_csv(SRC / f"{DATASET}.csv", sep=";")
    states = pd.read_csv(SRC / f"{DATASET}_C-W96-0.csv", sep=";")
    names = {c: n.split(" <")[0] for c, n in zip(states["code"], states["en_name"], strict=True)}
    raw["year"] = raw["C-SDB_TIT-0"] // 100
    total_2025 = raw.loc[raw["year"] == 2025, "F-UEB"].sum()
    if total_2025 != CHECK_2025_STAYS:
        raise SystemExit(f"2025 overnight stays sum to {total_2025:,}, expected {CHECK_2025_STAYS:,}: check the file")
    d = raw[raw["year"].between(FIRST, LAST)]
    g = d.groupby(["C-SDB_TIT-0", "C-W96-0"])[["F-ANK", "F-UEB"]].sum().reset_index()
    rows = []
    for _, r in g.iterrows():
        code, ym = r["C-W96-0"], str(r["C-SDB_TIT-0"])
        rid = REGION_ID[code]
        for col, (series, unit) in SERIES.items():
            rows.append({"region_id": rid, "region_name": names[code], "country": "Austria", "is_host": rid == HOST,
                         "month": f"{ym[:4]}-{ym[4:]}", "series": series, "value": int(r[col]), "unit": unit,
                         "source_name": "Statistik Austria, Nächtigungsstatistik (open data, CC BY 4.0)",
                         "source_url": META_URL, "table_id": DATASET, "retrieval_date": RETRIEVED,
                         "notes": HOST_NOTE if rid == HOST else DONOR_NOTE})
    out = pd.DataFrame(rows).sort_values(["region_id", "series", "month"])
    expected = 9 * 12 * (LAST - FIRST + 1) * 2
    if len(out) != expected:
        raise SystemExit(f"Expected {expected} rows, got {len(out)}: a state or month is missing")
    return out


def build_races() -> pd.DataFrame:
    rr = pd.read_csv(config.ROOT / "website" / "public" / "data" / "race_result.csv")
    races = rr[rr["circuit_id"] == CIRCUIT][["season", "race_name", "date"]].drop_duplicates().sort_values("date")
    rows = []
    for year, g in races.groupby("season"):
        days = [dt.date.fromisoformat(x) for x in g["date"]]
        start = min(days) - dt.timedelta(days=2)  # Friday of the first race weekend
        note = "Weekend start = race day minus 2 days (race results hold race day only)."
        if len(g) > 1:
            note += " Two races this year: " + "; ".join(f"{n} {d}" for n, d in zip(g["race_name"], g["date"], strict=True)) + "."
        if year == 2020:
            note += " Held without spectators (COVID-19)."
        rows.append({"region_id": HOST, "race_name": " / ".join(g["race_name"]), "year": int(year),
                     "race_start_date": start.isoformat(), "race_end_date": max(days).isoformat(),
                     "source_url": "https://api.jolpi.ca/ergast/f1/", "notes": note})
    return pd.DataFrame(rows)


def main() -> None:
    t, e = build_tourism(), build_races()
    t.to_csv(config.MANUAL_DIR / "gp_tourism_monthly.csv", index=False)
    e.to_csv(config.MANUAL_DIR / "gp_race_events.csv", index=False)
    print(f"gp_tourism_monthly.csv: {len(t)} rows ({t['region_id'].nunique()} states, {t['month'].min()} to {t['month'].max()})")
    print(f"gp_race_events.csv: {len(e)} race years ({e['year'].min()}-{e['year'].max()})")


if __name__ == "__main__":
    main()
