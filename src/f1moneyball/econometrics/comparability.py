"""Financial comparability: how well each team-season's accounts measure the team's racing resources.

Every classification comes from facts recorded in data/manual/financial_observations.csv (period dates,
accounting basis, comparability warnings and notes taken from the filings), never from a score. The rules:

Insufficient information
    No figure, or the accounting basis is not recorded.
Limited comparability (any of)
    * the accounts cover only part of the team (recorded warning: engineering bought in, or the racing
      licence held by another company);
    * the accounting period is shorter than 350 or longer than 380 days;
    * the basis (group or company accounts) differs from the team's previous season: a boundary change;
    * staff costs include recorded share-based payments (staff costs only).
Moderate comparability (any of, if not limited)
    * the financial year does not end in December, so it straddles two racing seasons;
    * the filing records discontinued operations (a change in what the company does).
High comparability
    None of the above.

The restricted-sample models below never treat a smaller sample as more reliable because its p-value is
smaller: they are reported next to the full sample with the number of team clusters each one keeps.
"""
from __future__ import annotations

import pandas as pd

METRICS = ("turnover", "staff_costs", "headcount")
ORDER = ["High", "Moderate", "Limited", "Insufficient information"]
PARTIAL_TEAM = ("bought in", "racing licence was held by")


def _days(r) -> float:
    try:
        return (pd.Timestamp(r.financial_year_end) - pd.Timestamp(r.financial_year_start)).days + 1
    except (TypeError, ValueError):
        return float("nan")


def classify(fin: pd.DataFrame) -> pd.DataFrame:
    """One row per team, season and resource measure: category, reasons and the filing they come from."""
    d = fin[fin["metric"].isin(METRICS) & fin["season_mapped"].notna()].copy()
    d["season"] = d["season_mapped"].astype(int)
    d = d.sort_values(["team_id", "metric", "season"])
    d["group"] = d["accounting_basis"].fillna("").str.contains("group")
    prev_basis = d.groupby(["team_id", "metric"])["accounting_basis"].shift()
    prev_season = d.groupby(["team_id", "metric"])["season"].shift()
    rows = []
    for (_, r), pb, ps in zip(d.iterrows(), prev_basis, prev_season, strict=True):
        warn, notes = str(r.comparability_warning or ""), str(r.notes or "")
        limited, moderate = [], []
        days = _days(r)
        if pd.isna(r.value) or not str(r.accounting_basis or "").strip() or r.accounting_basis != r.accounting_basis:
            cat, reasons = "Insufficient information", ["No figure or no recorded accounting basis"]
        else:
            if any(k in warn for k in PARTIAL_TEAM):
                limited.append("Accounts cover only part of the team")
            if days == days and not 350 <= days <= 380:
                limited.append(f"Accounting period of {int(days)} days")
            if isinstance(pb, str) and ps == r.season - 1 and pb != r.accounting_basis:
                limited.append(f"Boundary change: {pb.split('; ')[-1]} accounts last season, "
                               f"{r.accounting_basis.split('; ')[-1]} this season")
            if r.metric == "staff_costs" and "share-based payments" in notes:
                limited.append("Staff costs include share-based payments")
            if str(r.financial_year_end)[5:7] != "12":
                moderate.append("Financial year does not end in December")
            if "discontinued" in notes:
                moderate.append("Filing records discontinued operations")
            cat = "Limited" if limited else "Moderate" if moderate else "High"
            reasons = limited + moderate or ["Full year, same basis as last season, no recorded issue"]
        rows.append({"team_id": r.team_id, "season": r.season, "metric": r.metric, "category": cat,
                     "reasons": "; ".join(reasons), "accounting_basis": r.accounting_basis,
                     "period_days": None if days != days else int(days),
                     "source": f"{r.document_title} {r.document_page or ''}".strip(), "source_url": r.source_url})
    out = pd.DataFrame(rows)
    out["category"] = pd.Categorical(out["category"], ORDER, ordered=True)
    return out.sort_values(["metric", "team_id", "season"]).reset_index(drop=True)


def boundary_segments(fin: pd.DataFrame) -> pd.DataFrame:
    """team_id, season, segment: a new segment starts each time a team's accounting basis changes."""
    d = fin[(fin["metric"] == "turnover") & fin["season_mapped"].notna()].copy()
    d["season"] = d["season_mapped"].astype(int)
    d = d.sort_values(["team_id", "season"])
    d["basis"] = d["accounting_basis"].fillna("unknown")
    d["segment"] = d.groupby("team_id")["basis"].transform(lambda s: (s != s.shift()).cumsum())
    d["segment"] = d["team_id"] + "_" + d["segment"].astype(str)
    return d[["team_id", "season", "segment"]]
