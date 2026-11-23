"""Build the Singapore Grand Prix inputs from Singapore Tourism Board open data and race results.

Inputs (downloaded by hand, kept unchanged in data/source_documents/singapore_stb/):
  TotalVisitorInternationalArrivalsMonthly.csv
      data.gov.sg "Total Visitor International Arrivals, Monthly" (STB), Jan 1978 to Nov 2015.
  InternationalVisitorArrivalsByPlaceOfResidenceMonthly.csv
      data.gov.sg copy of SingStat table M550001, Jan 2008 onwards. First row = total arrivals.

The two series agree month by month from 2008 to Oct 2015 (Nov 2015 differs by 0.8%, a later
revision), which is checked below. The newer table is used from 2008, the older one before.

The series starts in January 2005: earlier years include the 1997-98 Asian crisis and the 2003
SARS outbreak, which a linear trend cannot absorb. Singapore has no comparison regions in this
dataset, so only the race-month event study runs; the synthetic control is skipped.

Run:  python -m f1moneyball.ingestion.singapore_stb
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from f1moneyball.ingestion.statistik_austria import replace_rows
from f1moneyball.utils import config

SRC = config.ROOT / "data" / "source_documents" / "singapore_stb"
OLD = "TotalVisitorInternationalArrivalsMonthly.csv"
NEW = "InternationalVisitorArrivalsByPlaceOfResidenceMonthly.csv"
OLD_URL = "https://data.gov.sg/datasets/d_33796e0e35e57890bdd6aa34364b898d/view"
NEW_URL = "https://data.gov.sg/datasets/d_d1c33009b674dcf70b8e8c790b793f28/view"
FIRST_MONTH, LAST_MONTH = "2005-01", "2025-12"
HOST, CIRCUIT, RETRIEVED = "sg_singapore", "marina_bay", "2026-11-19"
NOTE = ("Host: Marina Bay street circuit, night race every September from 2008 (none in 2020-2021). "
        "Total international visitor arrivals; no comparison regions, so event study only.")


def _new_series() -> pd.Series:
    raw = pd.read_csv(SRC / NEW)
    if not str(raw.iloc[0, 0]).strip().startswith("Total International Visitor Arrivals"):
        raise SystemExit(f"First row of {NEW} is not the total: {raw.iloc[0, 0]!r}")
    row = raw.iloc[0, 1:]
    idx = pd.PeriodIndex([pd.Period(f"{c[:4]}-{c[4:]}", freq="M") for c in row.index])
    return pd.Series(pd.to_numeric(row.replace("na", np.nan), errors="coerce").to_numpy(), index=idx).sort_index()


def build_tourism() -> pd.DataFrame:
    new = _new_series()
    old_raw = pd.read_csv(SRC / OLD)
    old = pd.Series(old_raw.iloc[:, 1].to_numpy(), index=pd.PeriodIndex(old_raw.iloc[:, 0], freq="M"))
    both = pd.concat([new.rename("new"), old.rename("old")], axis=1).dropna()
    agree = (both["new"] / both["old"] - 1).abs() < 0.01
    if not agree.all():
        raise SystemExit(f"Singapore series differ by more than 1% in {list(both.index[~agree].astype(str))}")
    s = pd.concat([old[old.index < new.index.min()], new]).sort_index()
    s = s[(s.index >= pd.Period(FIRST_MONTH, freq="M")) & (s.index <= pd.Period(LAST_MONTH, freq="M"))].dropna()
    rows = [{"region_id": HOST, "region_name": "Singapore", "country": "Singapore", "is_host": True,
             "month": str(m), "series": "arrivals", "value": int(v), "unit": "arrivals",
             "source_name": "Singapore Tourism Board via data.gov.sg (Singapore Open Data Licence)",
             "source_url": NEW_URL if m >= new.index.min() else OLD_URL,
             "table_id": "SingStat M550001" if m >= new.index.min() else "STB total visitor international arrivals, monthly",
             "retrieval_date": RETRIEVED, "notes": NOTE} for m, v in s.items()]
    return pd.DataFrame(rows)


# Races before the race-results window (which starts in 2010), from the same source:
# https://api.jolpi.ca/ergast/f1/circuits/marina_bay/races.json
EARLY_RACES = [(2008, "Singapore Grand Prix", "2008-09-28"), (2009, "Singapore Grand Prix", "2009-09-27")]


def build_races() -> pd.DataFrame:
    rr = pd.read_csv(config.ROOT / "website" / "public" / "data" / "race_result.csv")
    races = rr[rr["circuit_id"] == CIRCUIT][["season", "race_name", "date"]].drop_duplicates()
    early = pd.DataFrame(EARLY_RACES, columns=["season", "race_name", "date"])
    races = pd.concat([early[~early["season"].isin(races["season"])], races]).sort_values("date")
    rows = []
    for _, r in races.iterrows():
        day = dt.date.fromisoformat(r["date"])
        rows.append({"region_id": HOST, "race_name": r["race_name"], "year": int(r["season"]),
                     "race_start_date": (day - dt.timedelta(days=2)).isoformat(), "race_end_date": day.isoformat(),
                     "source_url": "https://api.jolpi.ca/ergast/f1/circuits/marina_bay/races.json",
                     "notes": "Weekend start = race day minus 2 days (race results hold race day only)."})
    return pd.DataFrame(rows)


def main() -> None:
    t, e = build_tourism(), build_races()
    replace_rows("gp_tourism_monthly.csv", t, "sg_")
    replace_rows("gp_race_events.csv", e, "sg_")
    print(f"Singapore: {len(t)} months ({t['month'].min()} to {t['month'].max()}), {len(e)} races")


if __name__ == "__main__":
    main()
