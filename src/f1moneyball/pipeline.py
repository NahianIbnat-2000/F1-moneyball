"""Command-line entry point.

    python -m f1moneyball.pipeline ingest   [--start 2010 --end 2025] [--force]
    python -m f1moneyball.pipeline build    # raw -> interim -> processed
    python -m f1moneyball.pipeline validate # writes reports/data_quality.{json,md}; exit 1 on errors
    python -m f1moneyball.pipeline publish  # validate, then write website/public/data
    python -m f1moneyball.pipeline all
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

import pandas as pd

from f1moneyball.econometrics.cost_cap import run_cost_cap
from f1moneyball.econometrics.efficiency import efficiency_table, financial_panel
from f1moneyball.econometrics.gp_economy import event_study as gp_event_study
from f1moneyball.econometrics.gp_economy import synthetic_control
from f1moneyball.econometrics.models import run_models
from f1moneyball.feature_engineering.competitive_balance import balance_table
from f1moneyball.feature_engineering.sporting import (
    LONG_STOP_S,
    constructor_season,
    enrich_results,
    gap_to_pole,
    pit_season,
    pit_stop_table,
)
from f1moneyball.ingestion import jolpica
from f1moneyball.ingestion.snapshot import constructor_season_from_snapshot
from f1moneyball.publishing.changelog import build_changelog
from f1moneyball.publishing.publish import publish_dataset, write_manifest
from f1moneyball.publishing.status import build_status
from f1moneyball.publishing.status import registry as load_registry
from f1moneyball.standardization.teams import add_team_id
from f1moneyball.utils import config
from f1moneyball.utils.http import RateLimitedClient
from f1moneyball.validation import checks

log = logging.getLogger("f1moneyball")


def _window(args) -> range:
    w = config.seasons()["study_window"]
    return range(args.start or w["start"], (args.end or w["end"]) + 1)


def cmd_ingest(args) -> None:
    cfg = config.sources()["jolpica"]
    client = RateLimitedClient(min_interval=cfg["min_seconds_between_requests"],
                               max_per_hour=cfg["rate_limit"]["sustained_per_hour"] - 50,
                               retrieval_log=config.METADATA_DIR / "retrieval_log.jsonl")
    for season in _window(args):
        log.info("Season %s", season)
        jolpica.download_season(season, client, force=args.force)
        jolpica.download_pit_stops(season, client, force=args.force)


def cmd_build(args) -> None:
    parts: dict[str, list[pd.DataFrame]] = {k: [] for k in jolpica.PARSERS}
    for season in _window(args):
        for kind, parser in jolpica.PARSERS.items():
            pages = jolpica.load_pages(season, kind)
            if pages:
                parts[kind].append(parser(pages))
    tables = {k: add_team_id(pd.concat(v, ignore_index=True)) for k, v in parts.items() if v}
    if "results" not in tables or "constructor_standings" not in tables:
        raise SystemExit("No raw data found. Run `ingest` first.")
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for k, df in tables.items():
        df.to_parquet(config.INTERIM_DIR / f"{k}.parquet", index=False)
    results = enrich_results(tables["results"])
    results.to_parquet(config.PROCESSED_DIR / "race_result.parquet", index=False)
    if "qualifying" in tables:
        gap_to_pole(tables["qualifying"]).to_parquet(config.PROCESSED_DIR / "qualifying.parquet", index=False)
    cs = constructor_season(tables["constructor_standings"], tables["results"], tables.get("qualifying"))
    stops = [jolpica.parse_pit_stops(p) for s in _window(args) if (p := jolpica.load_pages(s, "pit_stops"))]
    if stops:
        pits = pit_stop_table(pd.concat(stops, ignore_index=True), tables["results"])
        pits.to_parquet(config.PROCESSED_DIR / "pit_stop.parquet", index=False)
        cs = cs.merge(pit_season(pits), on=["season", "team_id"], how="left")
        log.info("Pit stops: %d (%d flagged as longer than %.0f s)", len(pits), int(pits["is_long_stop"].sum()), LONG_STOP_S)
    cs.to_parquet(config.PROCESSED_DIR / "constructor_season.parquet", index=False)
    balance = balance_table(cs)
    balance.to_parquet(config.PROCESSED_DIR / "competitive_balance.parquet", index=False)
    log.info("Built %d constructor-seasons", len(cs))
    eff = build_analysis(cs)
    cc_models, cc_es = run_cost_cap(balance, cs, eff)
    cc_models.to_parquet(config.PROCESSED_DIR / "cost_cap_models.parquet", index=False)
    if len(cc_es):
        cc_es.to_parquet(config.PROCESSED_DIR / "cost_cap_event_study.parquet", index=False)
    log.info("Cost cap models: %d rows (%d estimated)", len(cc_models), int(cc_models["estimated"].sum()))


def build_analysis(cs: pd.DataFrame) -> pd.DataFrame | None:
    """Efficiency indicators and models. Runs only when financial figures exist."""
    fin = pd.read_csv(config.MANUAL_DIR / "financial_observations.csv")
    for name in ("efficiency", "model_results"):
        (config.PROCESSED_DIR / f"{name}.parquet").unlink(missing_ok=True)
    if fin.empty or (fin["source_class"] == "missing").all():
        log.info("No financial figures entered: efficiency and models skipped")
        return None
    min_teams = load_registry()["financial_observation"].get("min_teams_per_season", 4)
    eff = efficiency_table(financial_panel(fin, cs), min_teams=min_teams)
    eff.to_parquet(config.PROCESSED_DIR / "efficiency.parquet", index=False)
    models = run_models(eff)
    if len(models):
        models.to_parquet(config.PROCESSED_DIR / "model_results.parquet", index=False)
    log.info("Efficiency rows: %d (%d included); models: %d", len(eff), int(eff["included"].sum()), len(models))
    return eff


def load_gp() -> tuple[pd.DataFrame, pd.DataFrame]:
    t = pd.read_csv(config.MANUAL_DIR / "gp_tourism_monthly.csv", dtype={"month": str})
    e = pd.read_csv(config.MANUAL_DIR / "gp_race_events.csv")
    if len(t):
        t["is_host"] = t["is_host"].astype(str).str.lower().isin({"true", "1", "yes"})
    return t, e


def build_gp() -> None:
    """Grand Prix Economy analysis. Inputs are manual, so this runs on every publish."""
    for name in ("gp_event_study", "gp_scm_path", "gp_scm_inference"):
        (config.PROCESSED_DIR / f"{name}.parquet").unlink(missing_ok=True)
    tourism, events = load_gp()
    if tourism.empty or events.empty:
        log.info("No Grand Prix tourism series or race dates entered: analysis skipped")
        return
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for series in sorted(tourism["series"].unique()):
        es = gp_event_study(tourism, events, series)
        path, inf = synthetic_control(tourism, events, series)
        for name, df in (("gp_event_study", es), ("gp_scm_path", path), ("gp_scm_inference", inf)):
            if len(df):
                f = config.PROCESSED_DIR / f"{name}.parquet"
                old = pd.read_parquet(f) if f.exists() else None
                pd.concat([old, df] if old is not None else [df]).to_parquet(f, index=False)


def cmd_build_snapshot(args) -> None:
    """Build sporting tables from the checked standings snapshot (used until the API pull runs)."""
    if any(config.RAW_DIR.glob("jolpica/*/constructor_standings_*.json")):
        raise SystemExit("Raw API data exists: run `build`, which supersedes the snapshot.")
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cs = constructor_season_from_snapshot()
    cs.to_parquet(config.PROCESSED_DIR / "constructor_season.parquet", index=False)
    balance = balance_table(cs)
    balance.to_parquet(config.PROCESSED_DIR / "competitive_balance.parquet", index=False)
    eff = build_analysis(cs)
    cc_models, cc_es = run_cost_cap(balance, cs, eff)
    cc_models.to_parquet(config.PROCESSED_DIR / "cost_cap_models.parquet", index=False)
    if len(cc_es):
        cc_es.to_parquet(config.PROCESSED_DIR / "cost_cap_event_study.parquet", index=False)
    log.info("Snapshot build: %d constructor-seasons, %d balance seasons", len(cs), len(balance))


def _load_processed() -> dict[str, pd.DataFrame]:
    out = {}
    for name in ("constructor_season", "competitive_balance", "race_result", "pit_stop", "efficiency", "model_results",
                 "cost_cap_models", "cost_cap_event_study", "gp_event_study", "gp_scm_path", "gp_scm_inference"):
        p = config.PROCESSED_DIR / f"{name}.parquet"
        if p.exists():
            out[name] = pd.read_parquet(p)
    out["regulation_event"] = pd.read_csv(config.MANUAL_DIR / "regulation_events.csv")
    out["financial_observation"] = pd.read_csv(config.MANUAL_DIR / "financial_observations.csv")
    out["gp_tourism_monthly"], out["gp_race_events"] = load_gp()
    return out


def run_validation(t: dict[str, pd.DataFrame]) -> list[checks.Issue]:
    issues: list[checks.Issue] = []
    team_ids = set(config.team_mapping()["lineages"])
    if "race_result" in t:
        r = t["race_result"]
        issues += checks.unique_key(r, ["season", "round", "driver_id"], "race_result")
        issues += checks.mapped_teams(r, "race_result")
        issues += checks.valid_seasons(r, "race_result")
        issues += checks.finishing_positions(r)
    if "constructor_season" in t:
        cs = t["constructor_season"]
        issues += checks.unique_key(cs, ["season", "team_id"], "constructor_season")
        issues += checks.mapped_teams(cs, "constructor_season")
        issues += checks.no_missing(cs, ["season", "team_id", "points", "position"], "constructor_season")
        issues += checks.season_points_positive(cs)
        if "race_result" in t:
            issues += checks.points_reconcile(cs, t["race_result"])
    if "pit_stop" in t:
        issues += checks.pit_stops(t["pit_stop"])
    if "efficiency" in t:
        issues += checks.unique_key(t["efficiency"], ["team_id", "season", "metric", "entity_name"], "efficiency")
    issues += checks.regulation_events(t["regulation_event"])
    issues += checks.financial_observations(t["financial_observation"], team_ids)
    issues += checks.gp_tourism(t["gp_tourism_monthly"])
    issues += checks.gp_events(t["gp_race_events"], t["gp_tourism_monthly"])
    return issues


def write_quality_report(issues: list[checks.Issue]) -> dict:
    errors = [i for i in issues if i.severity == "error"]
    summary = {"n_errors": len(errors), "n_warnings": len(issues) - len(errors),
               "issues": [i.to_dict() for i in issues]}
    out = config.REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "data_quality.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = ["# Data quality report", "", f"Errors: {summary['n_errors']}  ",
             f"Warnings: {summary['n_warnings']}", "", "| Dataset | Check | Severity | Rows | Message |",
             "|---|---|---|---|---|"]
    lines += [f"| {i.dataset} | {i.check} | {i.severity} | {i.n_rows} | {i.message} |" for i in issues]
    (out / "data_quality.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def cmd_validate(args) -> dict:
    summary = write_quality_report(run_validation(_load_processed()))
    log.info("Validation: %d errors, %d warnings", summary["n_errors"], summary["n_warnings"])
    if summary["n_errors"]:
        for i in summary["issues"]:
            if i["severity"] == "error":
                log.error("%s / %s: %s", i["dataset"], i["check"], i["message"])
        raise SystemExit(1)
    return summary


def cmd_publish(args) -> None:
    summary = cmd_validate(args)  # exits before writing anything if there are errors
    build_gp()
    t = _load_processed()
    entries, published = [], {}
    for name in ("constructor_season", "race_result", "pit_stop", "competitive_balance", "regulation_event",
                 "financial_observation", "efficiency", "model_results", "cost_cap_models", "cost_cap_event_study",
                 "gp_tourism_monthly", "gp_race_events", "gp_event_study", "gp_scm_path", "gp_scm_inference"):
        if name in t and len(t[name]):
            entries.append(publish_dataset(name, t[name]))
            published[name] = t[name]
    build_status(published, summary["issues"], record_log=True)
    build_changelog()
    path = write_manifest(entries, {"n_errors": summary["n_errors"], "n_warnings": summary["n_warnings"],
                                    "issues": summary["issues"]})
    log.info("Published %d datasets -> %s", len(entries), path)


def main(argv=None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(prog="f1moneyball")
    p.add_argument("command", choices=["ingest", "build", "build-snapshot", "validate", "publish", "all"])
    p.add_argument("--start", type=int)
    p.add_argument("--end", type=int)
    p.add_argument("--force", action="store_true", help="Re-download cached seasons")
    args = p.parse_args(argv)
    if args.command == "all":
        cmd_ingest(args)
        cmd_build(args)
        cmd_publish(args)
    else:
        {"ingest": cmd_ingest, "build": cmd_build, "build-snapshot": cmd_build_snapshot,
         "validate": cmd_validate, "publish": cmd_publish}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
