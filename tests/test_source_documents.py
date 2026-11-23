"""The source manifest covers every document, records a hash and status for each, and matches what is in the repository."""
import csv
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ROWS = list(csv.DictReader((ROOT / "data/metadata/source_documents.csv").open(encoding="utf-8")))


def test_manifest_check_passes():
    r = subprocess.run([sys.executable, "scripts/source_documents.py", "check"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_every_file_in_repository_is_listed():
    listed = {r["path"] for r in ROWS}
    on_disk = {p.relative_to(ROOT).as_posix() for p in (ROOT / "data/source_documents").rglob("*") if p.is_file()}
    assert on_disk <= listed, sorted(on_disk - listed)


def test_no_filing_is_redistributed():
    """Companies House filings and FIA documents are linked, never stored in the public repository."""
    for r in ROWS:
        if r["category"] in ("companies_house", "fia"):
            assert r["local_copy"] in ("removed", "private_archive"), r["path"]
            assert not (ROOT / r["path"]).exists(), r["path"]
            assert r["document_url"].startswith("https://"), r["path"]


def test_every_cited_filing_is_listed_with_its_use():
    fo = pd.read_csv(ROOT / "data/manual/financial_observations.csv", dtype=str)
    cited = fo["notes"].fillna("").str.extract(r"Local copy: (\S+\.pdf)")[0].dropna()
    by_path = {r["path"]: r for r in ROWS}
    assert set(cited) <= set(by_path)
    for path, n in cited.value_counts().items():
        assert int(by_path[path]["n_observations"]) == n, path


def test_financial_observations_carry_document_status():
    sys.path.insert(0, str(ROOT / "src"))
    from f1moneyball.publishing.sources import with_source_status
    fo = with_source_status(pd.read_csv(ROOT / "data/manual/financial_observations.csv"))
    has_doc = fo["notes"].fillna("").str.contains("Local copy:")
    assert (fo.loc[has_doc, "source_document_status"] != "not_recorded").all()
    assert len(fo) == len(pd.read_csv(ROOT / "data/manual/financial_observations.csv"))  # no rows lost or duplicated
