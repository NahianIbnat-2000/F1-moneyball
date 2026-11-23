"""Build dataset_status.json: one authoritative status record per dataset in config/datasets.yaml.

Status rules (applied in this order):
  * not in the published set            -> registry `status_if_absent` (e.g. not_yet_collected)
  * published, but coverage rule fails   -> insufficient_coverage (rows are still downloadable)
  * published                            -> published

`last_updated` changes only when the dataset's content hash (`version`) changes, so a
re-run of the pipeline with identical data does not look like an update.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from f1moneyball.utils import config

STATUSES = ("published", "not_yet_collected", "under_validation", "insufficient_coverage",
            "unavailable_at_source", "not_comparable")


def registry() -> dict:
    return config.load_yaml("datasets.yaml")


def content_version(df: pd.DataFrame) -> str:
    """Short, stable hash of the published content."""
    # Floats are written to 10 significant digits before hashing, so rounding noise between runs
    # (last-digit differences from linear algebra libraries) does not count as a new version.
    h = hashlib.sha256(df.to_csv(index=False, float_format="%.10g").encode("utf-8")).hexdigest()
    return h[:12]


def missingness(df: pd.DataFrame) -> dict[str, dict]:
    out = {}
    n = len(df)
    for c in df.columns:
        m = int(df[c].isna().sum() + (df[c].astype(str).str.strip() == "").sum() * (df[c].dtype == object))
        out[c] = {"missing": m, "share": round(m / n, 4) if n else None}
    return out


def _coverage_issue(dataset_id: str, df: pd.DataFrame, spec: dict) -> str | None:
    if dataset_id == "financial_observation":
        need = spec.get("min_teams_per_season", 0)
        real = df[df["source_class"] != "missing"]
        if real.empty:
            return "No observed figures yet."
        per_season = real.groupby("season_mapped")["team_id"].nunique()
        if per_season.max() < need:
            return (f"At most {int(per_season.max())} teams have figures in any one season; "
                    f"{need} are needed before resource shares can be compared.")
    if dataset_id == "efficiency" and not df["included"].any():
        return "No comparison group has enough teams yet. Rows are listed with the reason each one is excluded."
    if dataset_id in ("cost_cap_models", "gp_event_study", "gp_scm_inference") and "estimated" in df and not df["estimated"].any():
        return "Not enough data to estimate yet; each row states the rule it fails."
    if dataset_id == "model_results" and not df["estimated"].any():
        return "No model could be estimated yet; each row states the sample-size rule it fails."
    return None


def _previous(path: Path) -> dict:
    try:
        return {d["dataset_id"]: d for d in json.loads(path.read_text())["datasets"]}
    except Exception:  # noqa: BLE001 - first run, or unreadable file: start fresh
        return {}


def build_status(published: dict[str, pd.DataFrame], issues: list[dict],
                 out_dir: Path | None = None, record_log: bool = False) -> dict:
    out_dir = out_dir or config.WEBSITE_DATA_DIR
    path = out_dir / "dataset_status.json"
    prev = _previous(path)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    records = []
    for ds_id, spec in registry().items():
        df = published.get(ds_id)
        ds_issues = [i for i in issues if i["dataset"] == ds_id]
        warnings = [i["message"] for i in ds_issues if i["severity"] == "warning"]
        rec = {
            "dataset_id": ds_id, "dataset_name": spec["name"], "modules": spec.get("modules", []),
            "source_ids": spec.get("source_ids", []),
            "explanation": {
                "would_contain": spec["would_contain"], "why_unavailable": spec["why_unavailable"],
                "needed_for_publication": spec["needed_for_publication"],
            },
            "coverage_start": None, "coverage_end": None, "observation_count": 0, "variable_count": 0,
            "missingness": {}, "version": None, "last_updated": None,
            "validation_status": "not_run", "validation_warnings": warnings, "status_note": None,
        }
        if df is None or df.empty:
            rec["status"] = spec["status_if_absent"]
        else:
            version = content_version(df)
            old = prev.get(ds_id, {})
            season_col = next((c for c in ("season", "season_mapped") if c in df.columns), None)
            rec.update({
                "observation_count": int(len(df)), "variable_count": int(df.shape[1]),
                "missingness": missingness(df), "version": version,
                "last_updated": old.get("last_updated") if old.get("version") == version else now,
                "validation_status": "passed_with_warnings" if warnings else "passed",
            })
            if season_col:
                s = pd.to_numeric(df[season_col], errors="coerce").dropna()
                if len(s):
                    rec["coverage_start"], rec["coverage_end"] = int(s.min()), int(s.max())
            note = _coverage_issue(ds_id, df, spec)
            rec["status"] = "insufficient_coverage" if note else "published"
            rec["status_note"] = note
            if "data_source" in df.columns and df["data_source"].astype(str).str.contains("snapshot").any():
                rec["status_note"] = ("Final standings only (points, position, wins), from a checked snapshot of the "
                                      "Jolpica-F1 API. Race-level variables arrive with the automated pull.")
        assert rec["status"] in STATUSES, rec["status"]
        records.append(rec)
    from f1moneyball.publishing.changelog import record_dataset_changes
    if record_log:
        record_dataset_changes(prev, records)
    status = {"generated_at_utc": now, "statuses": list(STATUSES), "datasets": records}
    out_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    return status
