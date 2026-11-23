"""Project paths and YAML config loading."""
from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
PUBLISHED_DIR = DATA_DIR / "published"
MANUAL_DIR = DATA_DIR / "manual"
METADATA_DIR = DATA_DIR / "metadata"
WEBSITE_DATA_DIR = ROOT / "website" / "public" / "data"
REPORTS_DIR = ROOT / "reports"


@cache
def load_yaml(name: str) -> dict[str, Any]:
    with open(CONFIG_DIR / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def sources() -> dict[str, Any]:
    return load_yaml("sources.yaml")


def seasons() -> dict[str, Any]:
    return load_yaml("seasons.yaml")


def team_mapping() -> dict[str, Any]:
    return load_yaml("team_mapping.yaml")


def regulatory_period(season: int) -> str | None:
    for p in seasons()["regulatory_periods"]:
        if p["start"] <= season <= p["end"]:
            return p["label"]
    return None
