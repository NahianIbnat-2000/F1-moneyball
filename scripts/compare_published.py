"""Compare freshly regenerated datasets with the published reference copies.

Usage (from the repository root, after `python -m f1moneyball.pipeline publish`):

    python scripts/compare_published.py --reference <git ref, default HEAD> [--tol 1e-6]

For every CSV in website/public/data that exists in the reference commit, checks that the regenerated file has the
same columns and rows and that numeric values agree within the tolerance. New rows or columns are listed but do not
fail the check; changed or missing values do. Exit code 1 on any difference, so CI fails when published results move.
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "website" / "public" / "data"
# Columns that describe the build rather than the result.
VOLATILE = {"retrieved_at", "built_at", "generated_at_utc", "published_at", "retrieval_date"}
# Columns built only from the raw Jolpica-F1 API pull (git-ignored), not from the committed processed data.
# A clean checkout without network access cannot rebuild them; no model uses them.
# Free-text columns: not used to match rows, and a wording change is reported but does not fail the check.
FREE_TEXT = {"note", "notes", "description", "definition", "label", "title",
             "source_document_status", "source_document_url"}
# Columns renamed on purpose, old name -> new name (version 3.1).
RENAMED = {"efficiency.csv": {"efficiency_ratio": "points_to_resource_share_ratio"}}
RAW_ONLY = {"constructor_season.csv": {"median_pit_gap_s", "pit_races", "service_pit_stops"}}


def reference(ref: str, rel: str) -> pd.DataFrame | None:
    r = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, capture_output=True)
    return pd.read_csv(io.BytesIO(r.stdout)) if r.returncode == 0 else None


def compare(old: pd.DataFrame, new: pd.DataFrame, tol: float, skip: set[str] = frozenset(),
            text_changes: list[str] | None = None) -> list[str]:
    problems = []
    old = old.drop(columns=[c for c in skip if c in old.columns and c not in new.columns])
    missing_cols = [c for c in old.columns if c not in new.columns and c not in VOLATILE]
    if missing_cols:
        problems.append(f"columns missing: {missing_cols}")
    cols = [c for c in old.columns if c in new.columns and c not in VOLATILE]
    key = [c for c in cols if (pd.api.types.is_string_dtype(old[c]) or old[c].dtype == object)
           and not pd.api.types.is_bool_dtype(old[c]) and not old[c].isna().all() and c not in FREE_TEXT]
    o, n = old[cols].copy(), new[cols].copy()
    for d in (o, n):
        d["_k"] = d[key].astype("object").fillna("").astype(str).agg("|".join, axis=1) if key else d.index.astype(str)
        d["_i"] = d.groupby("_k").cumcount()
    m = o.merge(n, on=["_k", "_i"], how="left", suffixes=("", "__new"), indicator=True)
    lost = int((m["_merge"] == "left_only").sum())
    if lost:
        problems.append(f"{lost} reference rows not found")
    for c in cols:
        if c in key:
            continue
        a, b = m[c], m.get(f"{c}__new")
        if b is None:
            continue
        if pd.api.types.is_bool_dtype(a) or pd.api.types.is_bool_dtype(b):
            bad = a.astype(str) != b.astype(str)
        elif pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            diff = (a - b).abs()
            both_nan = a.isna() & b.isna()
            bad = (~both_nan) & ((diff > tol * (1 + a.abs())) | (a.isna() != b.isna()))
        else:
            bad = (a.astype(str) != b.astype(str)) & ~(a.isna() & b.isna())
        if bad.any():
            msg = f"{c}: {int(bad.sum())} values differ"
            if c in FREE_TEXT and text_changes is not None:
                text_changes.append(msg)
            else:
                problems.append(msg)
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", default="HEAD")
    ap.add_argument("--tol", type=float, default=1e-6)
    args = ap.parse_args()
    failed = 0
    for path in sorted(DATA.glob("*.csv")):
        rel = path.relative_to(ROOT).as_posix()
        old = reference(args.reference, rel)
        if old is None:
            print(f"NEW   {path.name} ({len(pd.read_csv(path))} rows, not in {args.reference})")
            continue
        new = pd.read_csv(path)
        ren = RENAMED.get(path.name, {})
        if ren:
            old = old.rename(columns=ren)
            print(f"NOTE  {path.name}: renamed columns {ren}")
        skip = RAW_ONLY.get(path.name, set())
        text: list[str] = []
        problems = compare(old, new, args.tol, skip, text)
        if text:
            print(f"TEXT  {path.name}: wording changed, values unaffected: " + "; ".join(text))
        if skip & (set(old.columns) - set(new.columns)):
            print(f"NOTE  {path.name}: raw-only columns not rebuilt: {sorted(skip)}")
        extra = len(new) - len(old)
        if problems:
            failed += 1
            print(f"DIFF  {path.name}: " + "; ".join(problems))
        else:
            print(f"OK    {path.name} ({len(old)} rows{f', {extra} new rows' if extra > 0 else ''})")
    print("Reproduction matches the published reference." if not failed else f"{failed} dataset(s) differ.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
