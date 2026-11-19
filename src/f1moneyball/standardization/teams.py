"""Map Jolpica constructor IDs to stable team lineages, and classify race status."""
from __future__ import annotations

import pandas as pd

from f1moneyball.utils import config


def constructor_to_team() -> dict[str, str]:
    out: dict[str, str] = {}
    for team_id, spec in config.team_mapping()["lineages"].items():
        for cid in spec["constructor_ids"]:
            if cid in out:
                raise ValueError(f"constructorId {cid!r} mapped to two lineages")
            out[cid] = team_id
    return out


def team_display_names() -> dict[str, str]:
    return {k: v["display_name"] for k, v in config.team_mapping()["lineages"].items()}


def add_team_id(df: pd.DataFrame, col: str = "constructor_id") -> pd.DataFrame:
    """Adds team_id. Unknown constructors get team_id = NA so validation can flag them."""
    mapping = constructor_to_team()
    out = df.copy()
    out["team_id"] = out[col].map(mapping)
    return out


# Status strings in the Ergast/Jolpica data. Mechanical vs incident is only identifiable
# where the source records a specific cause. From 2024 many retirements are recorded only
# as "Retired", so mechanical DNFs are UNDER-counted in recent seasons. See Methodology.
MECHANICAL = {
    "engine", "gearbox", "transmission", "clutch", "hydraulics", "electrical", "power unit",
    "power loss", "ers", "turbo", "mgu", "brakes", "suspension", "wheel", "wheel nut",
    "driveshaft", "fuel system", "fuel pressure", "fuel pump", "oil leak", "oil pressure",
    "water leak", "water pressure", "water pump", "overheating", "exhaust", "radiator",
    "battery", "electronics", "throttle", "steering", "differential", "cooling system",
    "mechanical", "technical", "vibrations", "front wing", "rear wing", "halfshaft",
    "puncture", "tyre", "pneumatics", "spark plugs", "energy store", "seat", "undertray",
}
INCIDENT = {"accident", "collision", "collision damage", "spun off", "damage", "debris"}


def classify_status(status: str) -> str:
    """Returns one of: finished, mechanical, incident, disqualified, not_started, unspecified, other."""
    s = (status or "").strip().lower()
    if s == "finished" or s.startswith("+") or s == "lapped":
        return "finished"
    if s in MECHANICAL:
        return "mechanical"
    if s in INCIDENT:
        return "incident"
    if s.startswith("disqualified") or s == "excluded":
        return "disqualified"
    if s in {"did not start", "did not qualify", "withdrew", "not classified", "107% rule"}:
        return "not_started"
    if s in {"retired", "dnf"}:
        return "unspecified"
    return "other"
