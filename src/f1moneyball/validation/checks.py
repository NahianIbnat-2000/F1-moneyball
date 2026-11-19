"""Data quality checks. Each check returns a list of Issue objects.

Severity "error" blocks publishing. Severity "warning" is shown in the quality report
and on the Methodology page but does not block.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import pandas as pd

from f1moneyball.utils.config import seasons


@dataclass
class Issue:
    dataset: str
    check: str
    severity: str  # "error" | "warning"
    message: str
    n_rows: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def _issue(ds, check, sev, msg, n=0) -> list[Issue]:
    return [Issue(ds, check, sev, msg, int(n))]


def unique_key(df: pd.DataFrame, key: list[str], ds: str) -> list[Issue]:
    dup = df.duplicated(key, keep=False)
    return _issue(ds, "unique_key", "error", f"Duplicate rows on key {key}", dup.sum()) if dup.any() else []


def no_missing(df: pd.DataFrame, cols: list[str], ds: str) -> list[Issue]:
    out = []
    for c in cols:
        n = df[c].isna().sum()
        if n:
            out += _issue(ds, f"no_missing:{c}", "error", f"{n} missing values in {c}", n)
    return out


def valid_seasons(df: pd.DataFrame, ds: str) -> list[Issue]:
    w = seasons()["study_window"]
    bad = ~df["season"].between(1950, max(w["end"], pd.Timestamp.today().year))
    return _issue(ds, "valid_seasons", "error", "Seasons outside 1950..current", bad.sum()) if bad.any() else []


def mapped_teams(df: pd.DataFrame, ds: str) -> list[Issue]:
    bad = df["team_id"].isna()
    if not bad.any():
        return []
    ids = sorted(df.loc[bad, "constructor_id"].dropna().unique())
    return _issue(ds, "mapped_teams", "error",
                  f"constructorIds missing from config/team_mapping.yaml: {ids}", bad.sum())


def finishing_positions(results: pd.DataFrame, ds: str = "race_result") -> list[Issue]:
    out: list[Issue] = []
    pos = results["position"].dropna()
    if (pos < 1).any():
        out += _issue(ds, "positions_positive", "error", "Finishing position < 1", (pos < 1).sum())
    n = results.groupby(["season", "round"])["driver_id"].transform("count")
    over = results["position"] > n
    if over.any():
        out += _issue(ds, "positions_le_field", "error", "Position larger than field size", over.sum())
    # The same classified position should not appear twice in one race.
    d = results.dropna(subset=["position"]).duplicated(["season", "round", "position"])
    if d.any():
        out += _issue(ds, "positions_unique", "error", "Repeated finishing position in a race", d.sum())
    return out


def points_reconcile(cs: pd.DataFrame, results: pd.DataFrame, ds: str = "constructor_season",
                     tolerance: float = 0.0) -> list[Issue]:
    """Standings points minus race-result points. Differences are EXPECTED for seasons with
    sprints (sprint points are not in the race results endpoint) and penalty deductions,
    so this is a warning that lists the seasons, not an error."""
    race_pts = results.groupby(["season", "team_id"])["points"].sum().rename("race_points")
    m = cs.set_index(["season", "team_id"]).join(race_pts)
    diff = (m["points"] - m["race_points"]).abs() > tolerance
    if not diff.any():
        return []
    seasons_hit = sorted({int(s) for s, _ in m.index[diff]})
    return _issue(ds, "points_reconcile", "warning",
                  f"Standings points differ from summed race points in seasons {seasons_hit} "
                  "(expected where sprint races or penalties apply)", diff.sum())


def season_points_positive(cs: pd.DataFrame, ds: str = "constructor_season") -> list[Issue]:
    tot = cs.groupby("season")["points"].sum()
    bad = tot[tot <= 0]
    return _issue(ds, "season_points_positive", "error", f"Seasons with zero total points: {list(bad.index)}",
                  len(bad)) if len(bad) else []


def pit_stops(df: pd.DataFrame) -> list[Issue]:
    ds = "pit_stop"
    out = unique_key(df, ["season", "round", "driver_id", "stop"], ds)
    out += no_missing(df, ["season", "round", "driver_id", "stop"], ds)
    bad = df["duration_s"].notna() & (df["duration_s"] <= 0)
    if bad.any():
        out += _issue(ds, "duration_positive", "error", "Pit stop durations must be positive", int(bad.sum()))
    no_team = df["team_id"].isna()
    if no_team.any():
        out += _issue(ds, "team_match", "warning", "Stops whose driver is not in that race's results", int(no_team.sum()))
    return out


# ----------------------------------------------------------------------------- financial
SOURCE_CLASSES = {"audited", "official_disclosure", "secondary_estimate", "derived_estimate", "missing"}
METRICS = {"revenue", "operating_costs", "operating_profit", "staff_costs", "estimated_budget",
           "sponsorship_revenue", "turnover", "profit_before_tax", "headcount"}
CONFIDENCE = {"high", "medium", "low"}
# Plausible ranges in millions of the original currency. A value outside triggers an error
# that must be fixed or explained in `notes` with the flag `range_override`.
PLAUSIBLE_MILLIONS = {
    "revenue": (0, 1500), "turnover": (0, 1500), "operating_costs": (0, 1500),
    "staff_costs": (0, 600), "estimated_budget": (0, 1000), "sponsorship_revenue": (0, 600),
    "operating_profit": (-600, 600), "profit_before_tax": (-600, 600), "headcount": (0, 3000),
}
FIN_KEY = ["team_id", "entity_name", "financial_year_end", "metric"]
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


def financial_observations(df: pd.DataFrame, valid_team_ids: set[str]) -> list[Issue]:
    ds = "financial_observation"
    out: list[Issue] = []
    if df.empty:
        return _issue(ds, "coverage", "warning", "No financial observations entered yet")
    out += unique_key(df, FIN_KEY, ds)
    out += no_missing(df, ["team_id", "entity_name", "metric", "currency", "source_class",
                           "financial_year_end", "confidence"], ds)
    for col, allowed in [("source_class", SOURCE_CLASSES), ("metric", METRICS), ("confidence", CONFIDENCE),
                         ("team_id", valid_team_ids)]:
        bad = ~df[col].isin(allowed)
        if bad.any():
            out += _issue(ds, f"enum:{col}", "error",
                          f"Invalid {col}: {sorted(df.loc[bad, col].astype(str).unique())}", bad.sum())
    bad_ccy = ~df["currency"].astype(str).str.match(CURRENCY_RE)
    if bad_ccy.any():
        out += _issue(ds, "currency_iso", "error", "Currency must be an ISO 4217 code", bad_ccy.sum())
    start = pd.to_datetime(df["financial_year_start"], errors="coerce")
    end = pd.to_datetime(df["financial_year_end"], errors="coerce")
    if end.isna().any():
        out += _issue(ds, "dates", "error", "Unparseable financial_year_end", end.isna().sum())
    seq = start.notna() & end.notna() & (end <= start)
    if seq.any():
        out += _issue(ds, "date_sequence", "error", "financial_year_end not after start", seq.sum())
    has_value = df["source_class"] != "missing"
    no_url = has_value & df["source_url"].fillna("").str.strip().eq("")
    if no_url.any():
        out += _issue(ds, "provenance", "error", "Non-missing value without source_url", no_url.sum())
    for col in ("document_title", "transformation"):
        blank = has_value & df.get(col, pd.Series("", index=df.index)).fillna("").astype(str).str.strip().eq("")
        if blank.any():
            out += _issue(ds, f"provenance:{col}", "error", f"Non-missing value without {col}", blank.sum())
    is_estimate = df["source_class"].isin({"secondary_estimate", "derived_estimate"})
    warn = df.get("comparability_warning", pd.Series("", index=df.index)).fillna("").astype(str).str.strip()
    no_warn = is_estimate & warn.eq("")
    if no_warn.any():
        out += _issue(ds, "comparability_warning", "error", "Estimate without a comparability_warning", no_warn.sum())
    no_val = has_value & pd.to_numeric(df["value"], errors="coerce").isna()
    if no_val.any():
        out += _issue(ds, "value_numeric", "error", "Non-missing row without numeric value", no_val.sum())
    vals = pd.to_numeric(df["value"], errors="coerce") / 1e6
    lo = df["metric"].map(lambda m: PLAUSIBLE_MILLIONS.get(m, (-1e9, 1e9))[0])
    hi = df["metric"].map(lambda m: PLAUSIBLE_MILLIONS.get(m, (-1e9, 1e9))[1])
    if "headcount" in set(df["metric"]):
        vals = vals.where(df["metric"] != "headcount", pd.to_numeric(df["value"], errors="coerce"))
    override = df["notes"].fillna("").str.contains("range_override")
    out_range = vals.notna() & ((vals < lo) | (vals > hi)) & ~override
    if out_range.any():
        out += _issue(ds, "plausible_range", "error", "Value outside documented plausible range",
                      out_range.sum())
    # Mixing bases inside one team-metric series is allowed but must be visible.
    mixed = df[has_value].groupby(["team_id", "metric"])["source_class"].nunique()
    if (mixed > 1).any():
        out += _issue(ds, "mixed_source_class", "warning",
                      f"Series mixing source classes: {[f'{a}/{b}' for a, b in mixed[mixed > 1].index]}",
                      int((mixed > 1).sum()))
    return out


def regulation_events(df: pd.DataFrame) -> list[Issue]:
    ds = "regulation_event"
    out = unique_key(df, ["event_id"], ds)
    out += no_missing(df, ["event_id", "effective_date", "season", "category", "title", "source_url"], ds)
    bad_cat = ~df["category"].isin({"financial", "technical", "sporting", "power_unit"})
    if bad_cat.any():
        out += _issue(ds, "enum:category", "error", "Invalid category", bad_cat.sum())
    unverified = ~df["verified_against_primary"].astype(bool)
    if unverified.any():
        out += _issue(ds, "primary_verification", "warning",
                      "Events not yet checked against the primary FIA document", unverified.sum())
    return out


# ----------------------------------------------------------------------------- grand prix economy
GP_SERIES = {"arrivals", "overnight_stays", "hotel_occupancy"}


def gp_tourism(df: pd.DataFrame) -> list[Issue]:
    ds = "gp_tourism_monthly"
    if df.empty:
        return _issue(ds, "coverage", "warning", "No monthly tourism series entered yet")
    out = unique_key(df, ["region_id", "month", "series"], ds)
    out += no_missing(df, ["region_id", "region_name", "is_host", "month", "series", "value", "source_url", "table_id"], ds)
    bad_month = ~df["month"].astype(str).str.match(r"^\d{4}-(0[1-9]|1[0-2])$")
    if bad_month.any():
        out += _issue(ds, "month_format", "error", "month must be YYYY-MM", bad_month.sum())
    bad_series = ~df["series"].isin(GP_SERIES)
    if bad_series.any():
        out += _issue(ds, "enum:series", "error", f"series must be one of {sorted(GP_SERIES)}", bad_series.sum())
    val = pd.to_numeric(df["value"], errors="coerce")
    if (val.isna() | (val < 0)).any():
        out += _issue(ds, "value", "error", "value must be a non-negative number", int((val.isna() | (val < 0)).sum()))
    occ = (df["series"] == "hotel_occupancy") & (val > 100)
    if occ.any():
        out += _issue(ds, "occupancy_range", "error", "hotel_occupancy is a percentage and cannot exceed 100", occ.sum())
    mixed = df.groupby(["region_id", "series"])["unit"].nunique()
    if (mixed > 1).any():
        out += _issue(ds, "unit_consistency", "error", "A region-series uses more than one unit", int((mixed > 1).sum()))
    return out


def gp_events(df: pd.DataFrame, tourism: pd.DataFrame) -> list[Issue]:
    ds = "gp_race_events"
    if df.empty:
        return _issue(ds, "coverage", "warning", "No race dates entered yet")
    out = unique_key(df, ["region_id", "year"], ds)
    out += no_missing(df, ["region_id", "year", "race_start_date", "source_url"], ds)
    start = pd.to_datetime(df["race_start_date"], errors="coerce")
    end = pd.to_datetime(df["race_end_date"], errors="coerce")
    if start.isna().any():
        out += _issue(ds, "dates", "error", "Unparseable race_start_date", start.isna().sum())
    if (end.notna() & (end < start)).any():
        out += _issue(ds, "date_sequence", "error", "race_end_date before race_start_date", int((end < start).sum()))
    if not tourism.empty:
        unknown = ~df["region_id"].isin(set(tourism["region_id"]))
        if unknown.any():
            out += _issue(ds, "region_match", "warning", "Race regions without a tourism series", unknown.sum())
    return out
