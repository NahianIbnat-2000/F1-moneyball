"""Write frontend-ready JSON + CSV and a manifest describing what was published.

The website reads manifest.json first. A dataset that is not in the manifest does not
exist as far as the UI is concerned, so nothing can be shown without a traceable source.
"""
from __future__ import annotations

import json
import math
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import yaml

from f1moneyball.publishing.status import content_version
from f1moneyball.utils import config


def dictionaries() -> dict:
    with open(config.METADATA_DIR / "dictionaries.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=config.ROOT,
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None


def _clean(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if hasattr(v, "item"):  # numpy scalar
        return _clean(v.item())
    return v


def publish_dataset(name: str, df: pd.DataFrame, out_dir: Path | None = None) -> dict:
    out_dir = out_dir or config.WEBSITE_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = dictionaries()[name]
    undocumented = [c for c in df.columns if c not in spec["columns"]]
    if undocumented:
        raise ValueError(f"{name}: columns missing from data dictionary: {undocumented}")
    cols = [c for c in spec["columns"] if c in df.columns]
    df = df[cols]
    rows = [[_clean(v) for v in r] for r in df.itertuples(index=False, name=None)]
    (out_dir / f"{name}.json").write_text(
        json.dumps({"name": name, "columns": cols, "rows": rows}, separators=(",", ":")),
        encoding="utf-8")
    df.to_csv(out_dir / f"{name}.csv", index=False)
    srcs = config.sources()
    default_source = ", ".join(srcs[s]["name"] for s in spec["sources"])
    columns = {
        c: {
            "source": default_source,
            "transformation": "None (as reported by the source)",
            "missing_treatment": "Left blank. Never imputed.",
            **spec["columns"][c],
        }
        for c in cols
    }
    entry = {
        "name": name, "title": spec["title"], "description": spec["description"], "key": spec["key"],
        "rows": len(df), "n_variables": len(cols), "columns": columns,
        "limitations": spec.get("limitations", []),
        "version": content_version(df),
        "sources": [{"id": s, "name": srcs[s]["name"],
                     "url": srcs[s].get("docs") or srcs[s].get("base_url"),
                     "rights": source_rights(srcs[s])} for s in spec["sources"]],
        "files": {"json": f"data/{name}.json", "csv": f"data/{name}.csv"},
    }
    if "season" in df.columns and len(df):
        entry["coverage"] = {"season_min": int(df["season"].min()), "season_max": int(df["season"].max())}
    return entry


RIGHTS_FIELDS = ("licence", "licence_url", "attribution", "restrictions", "status", "evidence", "checked")


def source_rights(src: dict) -> dict:
    """Licence record for one source. Missing information is reported as unknown, never guessed."""
    r = src.get("rights") or {}
    out = {k: (None if r.get(k) is None else str(r.get(k))) for k in RIGHTS_FIELDS}
    if not out["licence"]:
        out["licence"] = "Unknown"
    if out["status"] not in ("verified", "partly verified", "not verified"):
        out["status"] = "not verified"
    return out


def environment() -> dict:
    """Python and package versions used for this build (reproducibility)."""
    import platform
    from importlib.metadata import PackageNotFoundError, version
    pkgs = {}
    for name in ("pandas", "numpy", "scipy", "statsmodels", "pyarrow", "duckdb", "requests"):
        try:
            pkgs[name] = version(name)
        except PackageNotFoundError:
            pkgs[name] = None
    return {"python": platform.python_version(), "packages": pkgs}


def write_manifest(entries: list[dict], quality: dict, out_dir: Path | None = None,
                   is_demo: bool = False) -> Path:
    out_dir = out_dir or config.WEBSITE_DATA_DIR
    manifest = {
        "project": "F1 Moneyball",
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "pipeline_commit": _git_commit(),
        # The website shows a banner on every chart if this is ever true.
        "is_synthetic_demo": is_demo,
        "datasets": {e["name"]: e for e in entries},
        "status_file": "data/dataset_status.json",
        "changelog_file": "data/changelog.json",
        "environment": environment(),
        "quality": quality,
    }
    path = out_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path
