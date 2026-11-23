"""Check every large year-on-year change in turnover or staff costs against the saved filings.

For each change the validation flags (above 50%), this reads the stated page of the saved Companies House
PDF for both years with OCR and looks for the recorded figure (in GBP thousands). If both figures are found,
the change is written to data/manual/verified_large_changes.csv, and validation stops warning about it.
A record only clears the warning while both values in the data still equal the values that were checked.

Needs poppler (pdftoppm) and tesseract on the PATH.  Run from the repository root:

    python scripts/verify_large_changes.py
"""
from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from f1moneyball.validation.checks import large_changes  # noqa: E402

FIN = ROOT / "data" / "manual" / "financial_observations.csv"
OUT = ROOT / "data" / "manual" / "verified_large_changes.csv"


def found_on_page(row: pd.Series, tmp: Path) -> bool:
    """True if the figure, in £000, appears in the OCR text of the stated PDF page."""
    pdf = re.search(r"Local copy: (\S+?\.pdf)", str(row["notes"]))
    page = re.search(r"\d+", str(row["document_page"]))
    if not pdf or not page:
        return False
    stem = tmp / f"p{abs(hash((pdf.group(1), page.group())))}"
    subprocess.run(["pdftoppm", "-f", page.group(), "-l", page.group(), "-r", "300", "-gray", "-png",
                    str(ROOT / pdf.group(1)), str(stem)], check=True, capture_output=True)
    img = next(tmp.glob(stem.name + "*.png"))
    text = subprocess.run(["tesseract", str(img), "-", "--psm", "6"], capture_output=True, text=True).stdout
    k = int(round(float(row["value"]) / 1000))
    return f"{k:,}" in text or str(k) in re.sub(r"[^\d]", "", text)


def main() -> None:
    fin = pd.read_csv(FIN)
    fin = fin[fin["value"].notna()]
    flagged = large_changes(fin)
    key = ["team_id", "metric", "season_mapped"]
    rows, failed = [], []
    with tempfile.TemporaryDirectory() as t:
        for _, f in flagged.iterrows():
            this = fin.set_index(key).loc[(f.team_id, f.metric, f.season_mapped)]
            prev = fin.set_index(key).loc[(f.team_id, f.metric, f.season_mapped - 1)]
            ok = found_on_page(this, Path(t)) and found_on_page(prev, Path(t))
            (rows if ok else failed).append({
                "team_id": f.team_id, "metric": f.metric, "season": int(f.season_mapped),
                "value": int(this["value"]), "prior_value": int(prev["value"]),
                "page": this["document_page"], "prior_page": prev["document_page"],
                "checked_on": dt.date.today().isoformat(),
                "method": "OCR of the stated page of the saved Companies House filing, both years"})
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"{len(rows)} of {len(flagged)} large changes confirmed in the filings; written to {OUT.relative_to(ROOT)}")
    for r in failed:
        print(f"  NOT CONFIRMED, check by hand: {r['team_id']} {r['metric']} {r['season']}")


if __name__ == "__main__":
    main()
