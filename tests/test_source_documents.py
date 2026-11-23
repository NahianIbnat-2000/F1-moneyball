"""Every source document is listed with a hash; kept copies match it, removed copies have an official link."""
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROWS = list(csv.DictReader((ROOT / "data/metadata/source_documents.csv").open(encoding="utf-8")))


def test_local_copies_match_manifest():
    r = subprocess.run([sys.executable, "scripts/source_documents.py", "check"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_every_document_is_listed():
    listed = {r["path"] for r in ROWS}
    on_disk = {p.relative_to(ROOT).as_posix() for p in (ROOT / "data/source_documents").rglob("*") if p.is_file()}
    assert on_disk <= listed, sorted(on_disk - listed)


def test_removed_copies_have_official_link_and_hash():
    for r in ROWS:
        assert len(r["sha256"]) == 64
        if r["local_copy"] == "removed":
            assert r["document_url"].startswith("https://"), r["path"]


def test_cited_filings_are_listed():
    import pandas as pd
    fo = pd.read_csv(ROOT / "data/manual/financial_observations.csv", dtype=str)
    cited = set(fo["notes"].fillna("").str.extract(r"Local copy: (\S+\.pdf)")[0].dropna())
    assert cited <= {r["path"] for r in ROWS}
