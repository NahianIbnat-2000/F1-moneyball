"""Source-document manifest (data/metadata/source_documents.csv) joined to the financial observations.

Each financial figure names the filing it was read from ("Local copy: <path>" in its notes; the path is the
document's identifier, even where the file itself is no longer in the repository). This module adds the filing's
verification status and official link to every figure; the provenance explorer shows both.
"""
from __future__ import annotations

import pandas as pd

from f1moneyball.utils import config

MANIFEST = config.ROOT / "data" / "metadata" / "source_documents.csv"


def manifest() -> pd.DataFrame:
    return pd.read_csv(MANIFEST, dtype=str).fillna("")


def with_source_status(fin: pd.DataFrame) -> pd.DataFrame:
    """Add source_document_status and source_document_url to each financial observation."""
    m = manifest()[["path", "verification_status", "document_url"]]
    out = fin.copy()
    out["_doc"] = out["notes"].fillna("").str.extract(r"Local copy: (\S+?\.pdf)", expand=False)
    out = out.merge(m.rename(columns={"path": "_doc", "verification_status": "source_document_status",
                                      "document_url": "source_document_url"}), on="_doc", how="left")
    out["source_document_status"] = out["source_document_status"].fillna("not_recorded")
    out.loc[out["source_document_url"] == "", "source_document_url"] = pd.NA
    return out.drop(columns="_doc")


def unverified_figures(fin: pd.DataFrame) -> set[tuple[str, int, str]]:
    """(team_id, season, metric) of figures whose filing is not yet verified by hash."""
    f = fin if "source_document_status" in fin else with_source_status(fin)
    f = f[(f["source_document_status"] != "verified") & f["season_mapped"].notna()]
    return {(t, int(s), m) for t, s, m in zip(f["team_id"], f["season_mapped"], f["metric"], strict=True)}

