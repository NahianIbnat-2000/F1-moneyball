"""Research changelog: manual entries + automatic dataset entries -> changelog.json.

Automatic entries are written only when a dataset's content version changes, so a re-run
with identical data adds nothing. They are labelled `new_data` (first publication) or
`updated_data` (new or corrected rows: the entry links both versions). Corrections that
need an explanation are written by hand as `corrected_data`.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from f1moneyball.utils import config

CATEGORIES = {
    "new_data": "New data", "updated_data": "Updated data", "corrected_data": "Corrected data",
    "methodology": "Methodological change", "revised_analysis": "Revised analysis",
    "publication": "New research publication", "website": "Website change",
}
AUTO_LOG = "changelog_auto.jsonl"


def record_dataset_changes(old: dict[str, dict], new: list[dict], log_dir: Path | None = None) -> list[dict]:
    """Compare previous and new status records; append an entry for each changed version."""
    log = (log_dir or config.METADATA_DIR) / AUTO_LOG
    added = []
    today = datetime.now(timezone.utc).date().isoformat()
    for rec in new:
        if not rec.get("version"):
            continue
        prev = old.get(rec["dataset_id"], {})
        if prev.get("version") == rec["version"]:
            continue
        first = not prev.get("version")
        added.append({
            "date": today, "category": "new_data" if first else "updated_data",
            "title": f"{rec['dataset_name']} {'published' if first else 'updated'}",
            "detail": (f"{rec['observation_count']} rows, version {rec['version']}"
                       + ("" if first else f" (previously {prev['version']}, {prev.get('observation_count')} rows)")),
            "datasets": [rec["dataset_id"]], "automatic": True,
        })
    if added:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            for e in added:
                fh.write(json.dumps(e) + "\n")
    return added


def build_changelog(out_dir: Path | None = None, log_dir: Path | None = None, manual: Path | None = None) -> list[dict]:
    manual_path = manual or (config.MANUAL_DIR / "changelog.yaml")
    entries = []
    for e in yaml.safe_load(manual_path.read_text(encoding="utf-8")) or []:
        if e["category"] not in CATEGORIES:
            raise ValueError(f"Unknown changelog category {e['category']!r}")
        d = e["date"]
        entries.append({**e, "date": d.isoformat() if isinstance(d, date) else str(d), "automatic": False})
    log = (log_dir or config.METADATA_DIR) / AUTO_LOG
    if log.exists():
        entries += [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    entries.sort(key=lambda e: e["date"], reverse=True)
    out = out_dir or config.WEBSITE_DATA_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "changelog.json").write_text(json.dumps({"categories": CATEGORIES, "entries": entries}, indent=2),
                                        encoding="utf-8")
    return entries
