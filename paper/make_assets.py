"""Build every number, table and figure used in paper/main.tex from the published datasets.

Nothing in the paper is typed by hand: run this script, then compile main.tex.

    python paper/make_assets.py          # reads website/public/data, writes paper/generated/
    cd paper && latexmk -pdf main.tex

Source data: the same CSV files the website shows at
https://nahianibnat-2000.github.io/F1-moneyball/data
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("F1M_DATA", ROOT / "website" / "public" / "data"))
OUT = Path(__file__).resolve().parent / "generated"
OUT.mkdir(exist_ok=True)

STUDY = "does-money-buy-speed"
METRICS = (("turnover", "Turnover"), ("staff_costs", "Staff costs"), ("headcount", "Headcount"))
SPECS = (("pooled", "Pooled"), ("team_fe", "Team FE"), ("twfe", "Team and season FE"))
SHORT = {  # lineage labels used in tables and figures
    "red_bull": "Red Bull", "mercedes": "Mercedes", "mclaren": "McLaren", "williams": "Williams",
    "enstone": "Enstone (Renault, Lotus, Alpine)", "silverstone": "Silverstone (Force India, Racing Point, Aston Martin)",
    "banbury": "Banbury (Virgin, Marussia, Manor)", "leafield": "Leafield (Lotus Racing, Caterham)",
}
TINY = {"red_bull": "Red Bull", "mercedes": "Mercedes", "mclaren": "McLaren", "williams": "Williams",
        "enstone": "Enstone", "silverstone": "Silverstone", "banbury": "Manor", "leafield": "Caterham"}

# ---------------------------------------------------------------------------- load
status = {d["dataset_id"]: d for d in json.loads((DATA / "dataset_status.json").read_text())["datasets"]}
models = pd.read_csv(DATA / "model_results.csv").set_index("model_id")
rob = pd.read_csv(DATA / "robustness_checks.csv")
rob = rob[rob["study"] == STUDY]
eff = pd.read_csv(DATA / "efficiency.csv")
eff = eff[eff["included"]]
turn = eff[eff["metric"] == "turnover"]


def num(x: float, d: int = 3) -> str:
    """Number for LaTeX, with a proper minus sign."""
    return "" if pd.isna(x) else f"{x:.{d}f}".replace("-", "$-$")


def pval(x: float) -> str:
    """p-value with two decimals (three near 0.05); very small values shown as <0.01."""
    if x < 0.005:
        return "$<$0.01"
    return f"{x:.3f}" if 0.045 <= x < 0.055 else f"{x:.2f}"  # avoid "0.05" hiding which side of 0.05


def rk(check: str, metric: str, model: str = "twfe") -> pd.Series:
    return rob[(rob.check_id == check) & (rob.metric == metric) & (rob.model == model)].iloc[0]


# ---------------------------------------------------------------------------- numbers.tex
macros: dict[str, str] = {}


def mac(name: str, value: str) -> None:
    macros[name] = value


corr_season = turn.groupby("season").apply(lambda d: d.resource_share.corr(d.points_share))
eff_team = turn.groupby("team_id").points_to_resource_share_ratio.mean()
mac("NTeamSeasons", str(len(turn)))
mac("NTeams", str(turn.team_id.nunique()))
mac("FirstSeason", str(turn.season.min()))
mac("LastSeason", str(turn.season.max()))
mac("CorrAll", num(turn.resource_share.corr(turn.points_share), 2))
mac("CorrMin", num(corr_season.min(), 2)); mac("CorrMinYear", str(corr_season.idxmin()))
mac("CorrMax", num(corr_season.max(), 2)); mac("CorrMaxYear", str(corr_season.idxmax()))
TEAMKEY = (("mercedes", "Mercedes"), ("red_bull", "RedBull"), ("mclaren", "McLaren"), ("enstone", "Enstone"),
           ("williams", "Williams"), ("silverstone", "Silverstone"), ("banbury", "Manor"), ("leafield", "Caterham"))
avg_turn = eff[(eff.metric == "turnover") & eff.value.notna()].groupby("team_id").value.mean()
for tid, cs in TEAMKEY:
    mac(f"Eff{cs}", num(eff_team[tid], 2))
    mac(f"TurnAvg{cs}", f"{avg_turn[tid] / 1e6:.0f}")                  # average turnover, GBP m (as in Table 1)

for met, _ in METRICS:
    for sp, _ in SPECS:
        r = models.loc[f"{met}_{sp}"]
        key = {"turnover": "Turn", "staff_costs": "Staff", "headcount": "Head"}[met] + \
            {"pooled": "Pooled", "team_fe": "Fe", "twfe": "Twfe"}[sp]  # e.g. \CoefTurnFe
        mac(f"Coef{key}", num(r.coef)); mac(f"P{key}", pval(r.p_t))         # clustered, t(G - 1)
        mac(f"CiLow{key}", num(r.ci_t_low)); mac(f"CiHigh{key}", num(r.ci_t_high))
        if pd.notna(r.ci_boot_low):
            mac(f"CiBootLow{key}", num(r.ci_boot_low)); mac(f"CiBootHigh{key}", num(r.ci_boot_high))
        mac(f"Pp{key}", num(r.effect_10pct_pp, 1))
        b = rk("baseline", met, sp)
        if pd.notna(b.p_wild):
            mac(f"Pwild{key}", num(b.p_wild, 2))
mac("NObs", str(int(models.loc["turnover_pooled"].n_obs)))

loo = rob[rob.check_id == "leave_one_team_out"]
for met in ("turnover", "staff_costs"):
    s = loo[loo.metric == met].sort_values("coef")
    k = met.replace("_", "").title()
    mac(f"Loo{k}Min", num(s.coef.iloc[0])); mac(f"Loo{k}Max", num(s.coef.iloc[-1]))
for met in ("turnover", "staff_costs", "headcount"):
    r = rk("position_outcome", met)
    k = met.replace("_", "").title()
    mac(f"Pos{k}", num(r.coef, 2)); mac(f"PosP{k}", pval(r.p_t))
    mac(f"PosCiBootLow{k}", num(r.ci_boot_low, 2)); mac(f"PosCiBootHigh{k}", num(r.ci_boot_high, 2))
    mac(f"PosPwild{k}", "n/a" if pd.isna(r.p_wild) else pval(r.p_wild))
    mac(f"PosTen{k}", num(abs(r.coef) * np.log(1.1), 2))  # places gained per 10% more of the resource
# accounting comparability and multiple testing
sc, scp = rk("scope_control", "staff_costs"), rk("scope_control_position", "staff_costs")
mac("ScopeStaff", num(sc.coef)); mac("ScopePStaff", pval(sc.p_t)); mac("ScopePwildStaff", pval(sc.p_wild))
mac("ScopePosStaff", num(scp.coef, 2)); mac("ScopePosPwildStaff", pval(scp.p_wild))
mac("ScopeN", sc.note.split()[0])
an, sb = rk("annualised_periods", "staff_costs"), rk("staff_costs_ex_share_based_pay", "staff_costs")
mac("AnnStaff", num(an.coef)); mac("AnnPwildStaff", pval(an.p_wild))
mac("SbpStaff", num(sb.coef)); mac("SbpPwildStaff", pval(sb.p_wild))
holm = rob[rob.check_id == "holm_adjusted"]
hpos = holm[(holm.metric == "staff_costs") & holm.check.str.contains("position")].iloc[0]
mac("HolmPosStaff", pval(hpos.p_wild))
rest = holm.drop(hpos.name)
mac("HolmRestMin", pval(rest.p_wild.min())); mac("HolmRestMax", pval(rest.p_wild.max()))
mac("HolmN", str(len(holm)))
# Real terms: only reported once the pipeline has published the CPI-deflated rows (needs data/manual/uk_cpi_annual.csv).
rt = rob[rob.check_id == "real_terms"]
if len(rt):
    rs = rt[(rt.metric == "staff_costs") & (rt.model == "team_fe")].iloc[0]
    rb = rk("baseline", "staff_costs", "team_fe")
    mac("RealTerms", "A further check measures money in 2015 pounds with the UK consumer prices index \\citep{ons_cpi}. "
        "This cannot change the two-way model, because the season effects already absorb inflation that is common to all "
        f"teams. In the team-effects model the staff-cost coefficient moves from {num(rb.coef)} to {num(rs.coef)} "
        f"(bootstrap $p = {pval(rs.p_wild)}$), so the simpler models do not change in substance either. ")
    CLAIMS_EXTRA = {"real terms: team-effects staff estimate stays insignificant (Section 6)": rs.p_wild > 0.1}
else:
    mac("RealTerms", "")
    CLAIMS_EXTRA = {}
mac("NDroppedByLag", str(len(turn) - int(models.loc["turnover_pooled"].n_obs)))
mac("RsqBase", num(rk("baseline", "turnover").r2, 2))
mac("RsqOps", num(rk("h4_operations", "turnover").r2, 2))
for k in ("financial_observation", "efficiency", "model_results", "robustness_checks", "constructor_season"):
    mac("Ver" + k.replace("_", " ").title().replace(" ", ""), status[k]["version"])

# Cost-cap and rule-reset rows of Table 3, used in the text
cap = rk("h3_cap_interaction", "staff_costs")
mac("CapStaff", num(cap.coef)); mac("CapPStaff", pval(cap.p_t)); mac("CapPwildStaff", pval(cap.p_wild))
cap_t = rk("h3_cap_interaction", "turnover")
mac("CapTurn", num(cap_t.coef)); mac("CapPwildTurn", pval(cap_t.p_wild))
mac("NoResetStaff", num(rk("no_reset_seasons", "staff_costs").coef))
ops = rk("h4_operations", "staff_costs")
mac("OpsStaff", num(ops.coef))

# Comparable samples, other outcomes and timing (Section 6, Table 4)
for cid, key in (("sample_high_points_share", "HighPts"), ("sample_high_position", "HighPos"),
                 ("sample_high_moderate_points_share", "HighModPts"), ("sample_high_moderate_position", "HighModPos"),
                 ("segment_fe_points_share", "SegPts"), ("segment_fe_position", "SegPos"),
                 ("outcome_covered_share", "Covered"), ("outcome_norm_position", "NormPos"),
                 ("lag_two_seasons", "LagTwo"), ("reverse_direction", "Rev")):
    for met, mk in (("turnover", "Turn"), ("staff_costs", "Staff"), ("headcount", "Head")):
        r = rk(cid, met)
        d = 2 if cid.endswith("position") and not cid.startswith("outcome") else 3
        mac(f"{key}{mk}", num(r.coef, d)); mac(f"{key}P{mk}", pval(r.p_t)); mac(f"{key}Pwild{mk}", pval(r.p_wild))
        mac(f"{key}CiLow{mk}", num(r.ci_boot_low, d)); mac(f"{key}CiHigh{mk}", num(r.ci_boot_high, d))
        mac(f"{key}N{mk}", str(int(r.n_obs))); mac(f"{key}G{mk}", str(int(r.n_teams)))
fc = pd.read_csv(DATA / "financial_comparability.csv")
fct = fc[fc.metric == "turnover"].category.value_counts()
for cat, key in (("High", "High"), ("Moderate", "Moderate"), ("Limited", "Limited"), ("Insufficient information", "Insufficient")):
    mac(f"Comp{key}", str(int(fct.get(cat, 0))))
mac("CompTotal", str(int(fct.sum())))
mac("RevPerPpTurn", f"{rk('reverse_direction', 'turnover').coef:.1f}")   # % change in turnover per point of points share

# Plain-language scale for the main coefficients (Sections 5 and 6)
staff = eff[(eff.metric == "staff_costs") & eff.value.notna()]
mac("MedStaffM", f"{staff.value.median() / 1e6:.0f}")                  # median team staff costs, GBP m
mac("TenPctStaffM", f"{staff.value.median() / 1e7:.1f}")               # 10% of the median, GBP m
turn = eff[(eff.metric == "turnover") & eff.value.notna()]
mac("MedTurnM", f"{turn.value.median() / 1e6:.0f}")
mac("TenPctTurnM", f"{turn.value.median() / 1e7:.0f}")
for met, key in (("staff_costs", "Staff"), ("turnover", "Turn")):
    c = abs(rk("position_outcome", met).coef)
    mac(f"OnePlace{key}", f"{(np.exp(1 / c) - 1) * 100:.0f}")          # % more resource that goes with one place higher

# data construction (Appendix C) and reproduction (Appendix B)
fin = pd.read_csv(DATA / "financial_observation.csv")
fin = fin[fin["value"].notna()]
verified = pd.read_csv(ROOT / "data" / "manual" / "verified_large_changes.csv")
mac("NVerifiedChanges", str(len(verified)))
mac("NFinFigures", f"{len(fin):,}")
mac("NFilings", str(fin.drop_duplicates(["team_id", "financial_year_end"]).shape[0]))
rsrc = (ROOT / "src" / "f1moneyball" / "econometrics" / "robustness.py").read_text()
draws = int(re.search(r"B_DRAWS = (\d+)", rsrc).group(1))
mac("BootDraws", f"{draws:,}")
mac("BootSeed", re.search(r"seed: int = (\d+)", rsrc).group(1))

# Source documents (Appendix B): verification status from data/metadata/source_documents.csv
docs = pd.read_csv(ROOT / "data" / "metadata" / "source_documents.csv", dtype=str).fillna("")
ch = docs[docs.category == "companies_house"]
mac("NDocCH", str(len(ch))); mac("NDocVerified", str(int((ch.verification_status == "verified").sum())))
unv = ch[ch.verification_status != "verified"]
excl = rob[rob.check_id.str.startswith("exclude_unverified_sources")]
if len(unv) and len(excl):
    ep, eq = (rk("exclude_unverified_sources_points_share", "staff_costs"), rk("exclude_unverified_sources_position", "staff_costs"))
    mac("DocUnverified", f"For the other {len(unv)}, an official link has been found but not yet checked against the copy used; "
        f"those copies are held in a private archive until it is. Leaving out the {int(unv.n_observations.astype(int).sum())} "
        f"figures read from them ({int(ep.n_obs)} team-seasons and {int(ep.n_teams)} teams remain) gives a two-way staff-cost "
        f"coefficient of {num(ep.coef)} for points share (bootstrap $p = {pval(ep.p_wild)}$) and {num(eq.coef, 2)} places for "
        f"position (bootstrap $p = {pval(eq.p_wild)}$), close to the main estimates.")
    CLAIMS_EXTRA["unverified-source exclusion stays close to the main staff estimates (Appendix B)"] = (
        abs(ep.coef - rk("baseline", "staff_costs").coef) < 0.05 and abs(eq.coef - rk("position_outcome", "staff_costs").coef) < 0.5)
else:
    mac("DocUnverified", "")

# ---------------------------------------------------------------------------- claim checks
# main.tex makes a few statements in words that depend on the numbers. If new data make one of them
# false, stop here so the text is revised instead of silently going out of date.
pos = {m: rk("position_outcome", m) for m in ("turnover", "staff_costs", "headcount")}
CLAIMS = {
    "leave-one-out estimates never change sign (Section 6, abstract)":
        all((loo[loo.metric == m].coef > 0).all() for m in ("turnover", "staff_costs")),
    "team-FE-only turnover link is not significant (abstract, Section 7)": models.loc["turnover_team_fe"].p_t > 0.10,
    "TWFE estimates are positive for all three measures (abstract)":
        all(models.loc[f"{m}_twfe"].coef > 0 for m, _ in METRICS),
    "staff-cost points-share link: bootstrap p < 0.05, t(G-1) p > 0.05 (Section 5)":
        models.loc["staff_costs_twfe"].p_wild < 0.05 < models.loc["staff_costs_twfe"].p_t,
    "staff-cost points-share bootstrap interval only just excludes zero (Section 5)":
        0 < models.loc["staff_costs_twfe"].ci_boot_low < 0.01,
    "bootstrap intervals agree with bootstrap p at 5% for every within-team model (Section 5)":
        all((models.loc[f"{m}_{sp}"].p_wild < 0.05) == (models.loc[f"{m}_{sp}"].ci_boot_low > 0 or models.loc[f"{m}_{sp}"].ci_boot_high < 0)
            for m, _ in METRICS for sp in ("team_fe", "twfe")),
    "exactly one within-team bootstrap interval in Table 2 excludes zero (Section 5)":
        sum(models.loc[f"{m}_{sp}"].ci_boot_low > 0 or models.loc[f"{m}_{sp}"].ci_boot_high < 0
            for m, _ in METRICS for sp in ("team_fe", "twfe")) == 1,
    "every within-team t(G-1) interval in Table 2 includes zero (Section 5)":
        all(models.loc[f"{m}_{sp}"].ci_t_low < 0 < models.loc[f"{m}_{sp}"].ci_t_high for m, _ in METRICS for sp in ("team_fe", "twfe")),
    "restricted samples keep sign for staff costs, both outcomes (Section 6)":
        all(rk(c, "staff_costs").coef * sgn > 0 for c, sgn in (("sample_high_points_share", 1), ("sample_high_position", -1),
                                                              ("segment_fe_points_share", 1), ("segment_fe_position", -1))),
    "staff position: bootstrap p < 0.05 in high-comparability sample and with basis effects (Section 6)":
        rk("sample_high_position", "staff_costs").p_wild < 0.05 and rk("segment_fe_position", "staff_costs").p_wild < 0.05,
    "staff points share: bootstrap p > 0.05 in high-comparability sample and with basis effects (Section 6)":
        rk("sample_high_points_share", "staff_costs").p_wild > 0.05 and rk("segment_fe_points_share", "staff_costs").p_wild > 0.05,
    "reverse direction: turnover follows last season's points; t and bootstrap disagree at 5% (Section 6)":
        (lambda r: r.coef > 0 and r.p_t < 0.05 < r.p_wild)(rk("reverse_direction", "turnover")),
    "reverse direction: staff costs and headcount not significant (Section 6)":
        all(rk("reverse_direction", m).p_wild > 0.1 and rk("reverse_direction", m).p_t > 0.05 for m in ("staff_costs", "headcount")),
    "direction of the within-team link survives every check in Tables 3 and 4 (Section 6)":
        all(rk(c, m).coef > 0 for m, _ in METRICS for c in ("no_reset_seasons", "scope_control", "sample_high_points_share",
            "sample_high_moderate_points_share", "segment_fe_points_share", "outcome_covered_share", "lag_two_seasons"))
        and all(rk(c, m).coef < 0 for m, _ in METRICS for c in ("position_outcome", "scope_control_position",
            "sample_high_position", "sample_high_moderate_position", "segment_fe_position", "outcome_norm_position")),
    "two-season lag: no estimate significant at 5% (Section 6)":
        all(rk("lag_two_seasons", m).p_wild > 0.05 and rk("lag_two_seasons", m).p_t > 0.05 for m, _ in METRICS),
    "all three measures go with a better position (Section 6)": all(r.coef < 0 for r in pos.values()),
    "position: t(G-1) and bootstrap p agree on the 0.10 level (Section 6)":
        all(pd.notna(r.p_wild) and (r.p_t < 0.10) == (r.p_wild < 0.10) for r in pos.values()),
    "staff points share: not significant once accounting scope is controlled (abstract, Sections 5-6)":
        sc.p_wild > 0.05,
    "staff position: bootstrap p < 0.05 with and without the scope control (abstract, Section 6)":
        rk("position_outcome", "staff_costs").p_wild < 0.05 and scp.p_wild < 0.05,
    "scope control barely moves the staff points-share coefficient (abstract)":
        abs(sc.coef - rk("baseline", "staff_costs").coef) < 0.05,
    "no within-team result survives Holm at 5%; staff position is the smallest (abstract, Section 6)":
        (holm.p_wild > 0.05).all() and hpos.p_wild == holm.p_wild.min(),
    "team-FE turnover estimate much smaller than pooled (Section 5)":
        models.loc["turnover_team_fe"].coef < 0.5 * models.loc["turnover_pooled"].coef,
    **CLAIMS_EXTRA,
    "no measurable change under the cost cap (abstract, Section 6)":
        all(rk("h3_cap_interaction", m).p_t > 0.10 for m, _ in METRICS),
}
failed = [c for c, ok in CLAIMS.items() if not ok]
if failed:
    raise SystemExit("These statements in paper/main.tex are no longer true for the current data. "
                     "Revise the text, then rerun:\n  - " + "\n  - ".join(failed))

(OUT / "numbers.tex").write_text(
    "% Generated by paper/make_assets.py. Do not edit by hand.\n"
    + "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(macros.items())))

# ---------------------------------------------------------------------------- Table 1: descriptives
wide = eff.pivot_table(index=["team_id", "season"], columns="metric", values="value").reset_index()
wide = wide.merge(turn[["team_id", "season", "points_share", "points_to_resource_share_ratio"]], on=["team_id", "season"])
g = (wide.groupby("team_id")
     .agg(n=("season", "size"), a=("season", "min"), b=("season", "max"), t=("turnover", "mean"),
          s=("staff_costs", "mean"), h=("headcount", "mean"), ps=("points_share", "mean"), e=("points_to_resource_share_ratio", "mean"))
     .sort_values("t", ascending=False))
lines = []
for tid, r in g.iterrows():
    lines.append(f"{SHORT[tid]} & {int(r.a)}--{int(r.b)} ({int(r.n)}) & {r.t / 1e6:.0f} & {r.s / 1e6:.0f} & "
                 f"{r.h:.0f} & {r.ps * 100:.1f} & {r.e:.2f} \\\\")
(OUT / "table1_descriptives.tex").write_text("\n".join(lines) + "\n")

# ---------------------------------------------------------------------------- Table 2: main models
lines = []
for i, (met, lab) in enumerate(METRICS):
    for sp, sl in SPECS:
        r = models.loc[f"{met}_{sp}"]
        boot = "" if pd.isna(r.ci_boot_low) else f"[{num(r.ci_boot_low)}, {num(r.ci_boot_high)}]"
        lines.append(f"{lab if sp == 'pooled' else ''} & {sl} & {num(r.coef)} & {num(r.se)} & "
                     f"[{num(r.ci_t_low)}, {num(r.ci_t_high)}] & {pval(r.p_t)} & {boot} & "
                     f"{'' if pd.isna(r.p_wild) else pval(r.p_wild)} \\\\")
    if i < len(METRICS) - 1:
        lines.append("\\addlinespace")
(OUT / "table2_models.tex").write_text("\n".join(lines) + "\n")

# ---------------------------------------------------------------------------- Table 3: robustness
lines = []
for cid, lab in (("no_reset_seasons", "Without rule-reset seasons (2014, 2017, 2022)"),
                 ("position_outcome", "Outcome: championship position$^{b}$"),
                 ("h4_operations", "Add completion rate and grid-to-finish gain"),
                 ("h3_cap_interaction", "Interaction with cost-cap period$^{a}$")):
    for met, ml in METRICS:
        r = rk(cid, met)
        pv = pval(r.p_t) + (f" ({pval(r.p_wild)})" if pd.notna(r.p_wild) else "")
        base = "" if cid == "position_outcome" else num(rk("baseline", met).coef)
        lines.append(f"{lab if met == 'turnover' else ''} & {ml} & {num(r.coef)} & {pv} & {base} \\\\")
    lines.append("\\addlinespace")
for cid, lab in (("scope_control", "Control for group vs company accounts"),
                 ("scope_control_position", "Same control, outcome: position$^{b}$")):
    for met, ml in METRICS:
        r = rk(cid, met)
        base = num(rk("baseline" if cid == "scope_control" else "position_outcome", met).coef)
        lines.append(f"{lab if met == 'turnover' else ''} & {ml} & {num(r.coef)} & "
                     f"{pval(r.p_t)} ({pval(r.p_wild)}) & {base} \\\\")
    lines.append("\\addlinespace")
for cid, lab, mets in (("annualised_periods", "Accounting periods scaled to 12 months", ("turnover", "staff_costs")),
                       ("staff_costs_ex_share_based_pay", "Staff costs without share-based pay$^{c}$", ("staff_costs",))):
    for i, met in enumerate(mets):
        r = rk(cid, met)
        lines.append(f"{lab if i == 0 else ''} & {dict(METRICS)[met]} & {num(r.coef)} & {pval(r.p_t)} ({pval(r.p_wild)}) & "
                     f"{num(rk('baseline', met).coef)} \\\\")
    lines.append("\\addlinespace")
for met, ml in (("turnover", "Turnover"), ("staff_costs", "Staff costs")):
    s = loo[loo.metric == met].sort_values("coef")
    a, b = s.iloc[0], s.iloc[-1]
    lines.append(f"{'Leave one team out (range)' if met == 'turnover' else ''} & {ml} & {num(a.coef)} to {num(b.coef)} & "
                 f"without {TINY[a.dropped]} / {TINY[b.dropped]} & {num(rk('baseline', met).coef)} \\\\")
(OUT / "table3_robustness.tex").write_text("\n".join(lines) + "\n")

# ---------------------------------------------------------------------------- Table 4: comparable samples, outcomes, timing
lines = []
T4 = (("sample_high_points_share", "High comparability only; points share"),
      ("sample_high_moderate_points_share", "High or moderate comparability; points share"),
      ("segment_fe_points_share", "Team $\\times$ accounting-basis effects; points share"),
      ("sample_high_position", "High comparability only; position$^{a}$"),
      ("sample_high_moderate_position", "High or moderate comparability; position$^{a}$"),
      ("segment_fe_position", "Team $\\times$ accounting-basis effects; position$^{a}$"),
      ("outcome_covered_share", "Outcome: points share of covered teams"),
      ("outcome_norm_position", "Outcome: normalised position$^{b}$"),
      ("lag_two_seasons", "Resource lagged two seasons"),
      ("reverse_direction", "Reverse: log resource on last season's points share$^{c}$"))
for cid, lab in T4:
    for met, ml in METRICS:
        r = rk(cid, met)
        d = 2 if cid.endswith("_position") and not cid.startswith("outcome") else 3
        lines.append(f"{lab if met == 'turnover' else ''} & {ml} & {num(r.coef, d)} & [{num(r.ci_boot_low, d)}, "
                     f"{num(r.ci_boot_high, d)}] & {pval(r.p_t)} & {pval(r.p_wild)} & {int(r.n_obs)} & {int(r.n_teams)} \\\\")
    lines.append("\\addlinespace")
(OUT / "table4_samples_timing.tex").write_text("\n".join(lines[:-1]) + "\n")

# ---------------------------------------------------------------------------- Table C1: unusual periods
def tex_amp(x: str) -> str:
    return x.replace("&", r"\&")


per = fin.drop_duplicates(["team_id", "financial_year_end"]).copy()
per["days"] = (pd.to_datetime(per.financial_year_end) - pd.to_datetime(per.financial_year_start)).dt.days + 1
per = per[(per.days < 350) | (per.days > 380)].sort_values(["team_id", "financial_year_end"])
lines = []
for r in per.itertuples():
    season = "not used (stub)" if pd.isna(r.season_mapped) else str(int(r.season_mapped))
    lines.append(f"{SHORT[r.team_id]} & {tex_amp(r.entity_name)} & {r.financial_year_start} to {r.financial_year_end} & "
                 f"{r.days} & {season} \\\\")
(OUT / "tableC1_periods.tex").write_text("\n".join(lines) + "\n")

# ---------------------------------------------------------------------------- Table C2: accounting scope
sc_rows = fin[fin.metric == "turnover"].dropna(subset=["season_mapped"]).copy()
sc_rows["group"] = sc_rows.accounting_basis.fillna("").str.contains("group")


def spans(years: list[int]) -> str:
    """2014, 2015, 2016, 2019 -> 2014--2016, 2019"""
    out, start = [], None
    for i, y in enumerate(years):
        start = y if start is None else start
        if i == len(years) - 1 or years[i + 1] != y + 1:
            out.append(str(y) if y == start else f"{start}--{y}")
            start = None
    return ", ".join(out)


lines = []
for tid in g.index:
    t = sc_rows[sc_rows.team_id == tid]
    grp = sorted(int(y) for y in t[t.group].season_mapped)
    comp = sorted(int(y) for y in t[~t.group].season_mapped)
    lines.append(f"{SHORT[tid]} & {spans(comp) or '--'} & {spans(grp) or '--'} \\\\")
(OUT / "tableC2_scope.tex").write_text("\n".join(lines) + "\n")

# ---------------------------------------------------------------------------- figures
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix",  # Times-style, ships with matplotlib
                     "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#444444", "axes.labelcolor": "#222222", "xtick.color": "#444444",
                     "ytick.color": "#444444", "pdf.fonttype": 42})
# Okabe-Ito palette (colour-blind safe) plus a different marker per team, so colour is never the only cue.
OKABE = ["#0072B2", "#009E73", "#D55E00", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#999999"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]
order = g.index.tolist()

fig, ax = plt.subplots(figsize=(6.2, 4.3))
lim = max(turn.resource_share.max(), turn.points_share.max()) * 100 * 1.05
ax.plot([0, lim], [0, lim], color="#999999", lw=0.8, ls="--", zorder=1)
ax.text(lim * 0.97, lim * 0.93, "points share = turnover share", ha="right", va="top", fontsize=7.5, color="#666666", rotation=33)
for tid, c, mk in zip(order, OKABE, MARKERS):
    d = turn[turn.team_id == tid]
    ax.scatter(d.resource_share * 100, d.points_share * 100, s=34 if mk in "PX*" else 24, color=c, marker=mk, edgecolor="white", linewidth=0.3,
               label=TINY[tid], zorder=3)
ax.set_xlim(0, lim); ax.set_ylim(0, lim)
ax.set_xlabel("Turnover share among covered teams (%)")
ax.set_ylabel("Points share among covered teams (%)")
ax.grid(color="#e5e5e5", lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=7.5, loc="upper left", ncol=2, handletextpad=0.3, columnspacing=1.0)
fig.tight_layout(); fig.savefig(OUT / "fig1_scatter.pdf"); plt.close(fig)

fig, axes = plt.subplots(1, 3, figsize=(6.2, 2.5), sharey=True)
for ax, (met, lab) in zip(axes, METRICS):
    for j, (sp, sl) in enumerate(SPECS):
        r = models.loc[f"{met}_{sp}"]
        lo, hi = (r.ci_t_low, r.ci_t_high) if pd.isna(r.ci_boot_low) else (r.ci_boot_low, r.ci_boot_high)
        ax.errorbar(r.coef, j, xerr=[[r.coef - lo], [hi - r.coef]], fmt="o", ms=4,
                    color="#0072B2", ecolor="#0072B2", elinewidth=1.4, capsize=0)
    ax.axvline(0, color="#999999", lw=0.8, ls="--")
    ax.set_title(lab, fontsize=9)
    ax.set_yticks(range(3)); ax.set_yticklabels([s for _, s in SPECS])
    ax.invert_yaxis() if ax is axes[0] else None
    ax.grid(axis="x", color="#e5e5e5", lw=0.6); ax.set_axisbelow(True)
axes[1].set_xlabel("Coefficient on log resource in previous season (95% interval)")
fig.tight_layout(); fig.savefig(OUT / "fig2_coefficients.pdf"); plt.close(fig)

print(f"Wrote {len(macros)} numbers, 4 tables and 2 figures to {OUT}")
