import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import ChartFrame from "../components/ChartFrame";
import DataTable from "../components/DataTable";
import Plot from "../components/Plot";
import { Callout, PageHeader, Section } from "../components/Ui";
import { datasetUrl, useDataset, type Row } from "../lib/data";
import { ACCENT, MUTED, SERIES } from "../lib/chartTheme";

// Econometrics Lab. Shows only estimates the pipeline has published (model_results, robustness_checks).
// Nothing is estimated in the browser, and no number on this page is typed by hand.

const REPO = "https://github.com/NahianIbnat-2000/F1-moneyball/blob/main/";
const PAPER = "papers/Ibnat_Does_Money_Buy_Speed_working_paper.pdf";
const MEASURES: [string, string][] = [["turnover", "Turnover"], ["staff_costs", "Staff costs"], ["headcount", "Headcount"]];
const OUTCOMES: [string, string][] = [["points_share", "Share of championship points"], ["position", "Championship position"]];
const SPECS: { id: string; label: string; constant: string; reading: string }[] = [
  { id: "pooled", label: "Pooled (between teams)",
    constant: "Nothing. Every team-season is compared with every other.",
    reading: "Do teams with more money than other teams do better? Mixes lasting differences between teams with year-to-year changes." },
  { id: "team_fe", label: "Team fixed effects",
    constant: "Everything about a team that does not change over time (history, location, culture, owner).",
    reading: "Does a team do better in seasons after it had more money than its own average?" },
  { id: "twfe", label: "Team and season fixed effects",
    constant: "Lasting team differences, and everything that affects all teams in the same season (rules, inflation, prize money).",
    reading: "The main within-team test: compared with its own average and with the other teams that season, does more money come before better results?" },
];
// Robustness checks shown for the two-way model, in reading order. Labels come from the data; this only orders them.
// Only checks measured in the same units as the main estimate are plotted; the reverse direction and the normalised
// position have other units and are shown in the timing note instead.
const CHECK_ORDER = ["baseline", "no_reset_seasons", "annualised_periods", "scope_control", "staff_costs_ex_share_based_pay",
  "sample_high_points_share", "sample_high_moderate_points_share", "segment_fe_points_share", "outcome_covered_share",
  "lag_two_seasons", "h4_operations"];
const POSITION_CHECKS = ["position_outcome", "scope_control_position", "sample_high_position", "sample_high_moderate_position",
  "segment_fe_position"];

const SHORT: Record<string, string> = { pooled: "Pooled", team_fe: "Team FE", twfe: "Team + season FE" };
const narrowScreen = () => typeof window !== "undefined" && window.innerWidth < 640;
/** Break a long label into lines of about `w` characters so it fits beside a chart on small screens. */
function wrap(s: string, w: number) {
  const out: string[] = []; let line = "";
  for (const word of s.split(" ")) {
    if ((line + " " + word).trim().length > w && line) { out.push(line); line = word; } else line = (line + " " + word).trim();
  }
  return [...out, line].join("<br>");
}
const n = (v: Row[string]) => (v === null || v === undefined || v === "" ? NaN : Number(v));
const f3 = (v: number) => (Number.isFinite(v) ? v.toFixed(3).replace("-", "−") : "n/a");
const fp = (v: number) => (!Number.isFinite(v) ? "n/a" : v < 0.005 ? "<0.01" : v >= 0.045 && v < 0.055 ? v.toFixed(3) : v.toFixed(2));
/** Intervals for one published row: clustered with t(G - 1), and the bootstrap interval where it was computed. */
function intervals(r: Row) {
  const tLo = n(r.ci_t_low), tHi = n(r.ci_t_high), bLo = n(r.ci_boot_low), bHi = n(r.ci_boot_high);
  const boot = Number.isFinite(bLo) && Number.isFinite(bHi);
  return { tLo, tHi, bLo, bHi, lo: boot ? bLo : tLo, hi: boot ? bHi : tHi };
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="label">{label}</span>
      <select className="bg-surface border border-line px-3 py-2 min-h-11 font-mono text-sm" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </label>
  );
}

/** lo/hi: the interval drawn (bootstrap where computed, otherwise clustered with t(G - 1)). */
interface Est { spec: string; label: string; coef: number; se: number; lo: number; hi: number; tLo: number; tHi: number; bLo: number; bHi: number; p: number; pWild: number; pHolm: number; nObs: number; nTeams: number; nSeasons: number; r2: number; per10: number }

export default function Lab() {
  const models = useDataset("model_results");
  const rob = useDataset("robustness_checks");
  const [measure, setMeasure] = useState("staff_costs");
  const [outcome, setOutcome] = useState("points_share");
  const ready = models.status === "ready" && rob.status === "ready";
  const narrow = narrowScreen();

  const ests: Est[] = useMemo(() => {
    if (!ready) return [];
    const mb = rob.rows.filter((r) => r.study === "does-money-buy-speed" && r.metric === measure);
    const holmFor = (spec: string) => {
      const want = outcome === "points_share" ? "points share" : "championship position";
      const h = mb.find((r) => r.check_id === "holm_adjusted" && r.model === spec && String(r.check).includes(want));
      return h ? n(h.p_wild) : NaN;
    };
    return SPECS.map((s) => {
      if (outcome === "points_share") {
        const m = models.rows.find((r) => r.metric === measure && r.model_id === `${measure}_${s.id}`);
        const b = mb.find((r) => r.check_id === "baseline" && r.model === s.id);
        if (!m) return null;
        return { spec: s.id, label: s.label, coef: n(m.coef), se: n(m.se), ...intervals(m), p: n(m.p_t),
          pWild: b ? n(b.p_wild) : NaN, pHolm: holmFor(s.id), nObs: n(m.n_obs), nTeams: n(m.n_teams), nSeasons: n(m.n_seasons),
          r2: n(m.r2), per10: n(m.effect_10pct_pp) };
      }
      const r = mb.find((x) => x.check_id === "position_outcome" && x.model === s.id);
      if (!r) return null;
      return { spec: s.id, label: s.label, coef: n(r.coef), se: n(r.se), ...intervals(r), p: n(r.p_t),
        pWild: n(r.p_wild), pHolm: holmFor(s.id), nObs: n(r.n_obs), nTeams: n(r.n_teams), nSeasons: NaN, r2: n(r.r2),
        per10: n(r.coef) * Math.log(1.1) };
    }).filter((e): e is Est => e !== null);
  }, [ready, models.rows, rob.rows, measure, outcome]);

  const checks = useMemo((): { rows: Row[]; loo: Row[] } => {
    if (!ready) return { rows: [], loo: [] };
    const mb = rob.rows.filter((r) => r.study === "does-money-buy-speed" && r.metric === measure && r.model === "twfe");
    const wanted = outcome === "points_share" ? CHECK_ORDER : POSITION_CHECKS;
    const rows = wanted.map((c) => mb.find((r) => r.check_id === c)).filter((r): r is Row => Boolean(r))
      .map((r) => { const iv = intervals(r); return { ...r, plot_low: iv.lo, plot_high: iv.hi }; });
    const loo = mb.filter((r) => r.check_id === "leave_one_team_out");
    return { rows, loo };
  }, [ready, rob.rows, measure, outcome]);

  const timing = useMemo(() => {
    if (!ready) return null;
    const mb = rob.rows.filter((r) => r.study === "does-money-buy-speed" && r.metric === measure && r.model === "twfe");
    return { rev: mb.find((r) => r.check_id === "reverse_direction"), norm: mb.find((r) => r.check_id === "outcome_norm_position") };
  }, [ready, rob.rows, measure]);

  const mLabel = MEASURES.find(([v]) => v === measure)?.[1] ?? measure;
  const yLabel = outcome === "points_share" ? "points share (0 to 1)" : "places in the championship";
  const unitNote = outcome === "points_share"
    ? "Coefficient: change in points share (0 to 1) per one-unit change in the log of last season's resource. The per-10% column converts it to percentage points."
    : "Coefficient: change in championship position per log point of last season's resource. Negative means a better (lower) position.";

  return (
    <>
      <PageHeader eyebrow="Econometrics Lab" title="Explore the estimates"
        lede="Compare every published specification of Study 01 side by side: how the estimate changes between models, how uncertain it is, and whether it survives the robustness checks. Nothing here is re-estimated in your browser; every number comes from the published result files." />

      <Section>
        <h2 className="sr-only">Estimates and robustness checks</h2>
        {!ready && <p className="font-mono text-sm text-muted">{models.status === "missing" || rob.status === "missing" ? "Results not published yet." : "Loading published results…"}</p>}
        {ready && (
          <div className="grid gap-12">
            <ChartFrame
              meta={{
                id: "LAB-1", dataset: models.entry, methodology: "models",
                title: `${mLabel} last season and ${outcome === "points_share" ? "points share" : "championship position"}: three models`,
                caption: "Each row is one model. The dot is the estimate. The line is the 95% wild cluster bootstrap interval for the two fixed-effects models and the 95% clustered interval with t(G − 1) for the pooled model. A line that crosses the dashed zero line means the data are also consistent with no link.",
                source: outcome === "points_share" ? "model_results dataset; bootstrap and Holm p-values from robustness_checks." : "robustness_checks dataset (position_outcome rows).",
                shows: "Association between last season's money and this season's result, under three ways of comparing teams.",
                doesNotShow: "A causal effect. Success raises income too, and a one-season lag only reduces that problem.",
                summary: ests.map((e) => `${e.label}: ${f3(e.coef)} (95% interval ${f3(e.lo)} to ${f3(e.hi)}).`).join(" "),
              }}
              controls={<>
                <Select label="Money measure" value={measure} onChange={setMeasure} options={MEASURES} />
                <Select label="Outcome" value={outcome} onChange={setOutcome} options={OUTCOMES} />
              </>}
              table={<EstTable ests={ests} outcome={outcome} />}>
              <Plot ariaLabel={`Coefficient plot, ${mLabel}, ${outcome}`} height={300}
                data={[{
                  type: "scatter", mode: "markers", orientation: "h",
                  x: ests.map((e) => e.coef), y: ests.map((e) => (narrow ? SHORT[e.spec] : e.label)),
                  error_x: { type: "data", symmetric: false, array: ests.map((e) => e.hi - e.coef), arrayminus: ests.map((e) => e.coef - e.lo), color: SERIES, thickness: 2, width: 0 },
                  marker: { size: 11, color: SERIES },
                  hovertemplate: "<b>%{y}</b><br>coef %{x:.3f}<extra></extra>",
                }]}
                layout={{
                  margin: { l: 10, r: 16, t: 10, b: 50 },
                  xaxis: { title: { text: narrow ? "coefficient" : `coefficient (${yLabel} per log point)` }, zeroline: false },
                  yaxis: { autorange: "reversed", automargin: true },
                  shapes: [{ type: "line", x0: 0, x1: 0, yref: "paper", y0: 0, y1: 1, line: { color: MUTED, dash: "dash", width: 1 } }],
                }} />
              <p className="mt-2 text-sm text-muted max-w-3xl">{unitNote}</p>
            </ChartFrame>

            <div>
              <h2 className="label mb-3">How to read each model</h2>
              <div className="grid md:grid-cols-3 gap-4">
                {SPECS.map((s) => {
                  const e = ests.find((x) => x.spec === s.id);
                  if (!e) return null;
                  const crosses = e.lo <= 0 && e.hi >= 0;
                  const width = e.hi - e.lo;
                  const boot = Number.isFinite(e.bLo);
                  const tCrosses = e.tLo <= 0 && e.tHi >= 0;
                  return (
                    <article key={s.id} className="border border-line bg-surface p-4">
                      <h3 className="font-display uppercase text-lg text-head">{s.label}</h3>
                      <dl className="mt-2 grid gap-2 text-sm">
                        <div><dt className="label">The question</dt><dd>{s.reading}</dd></div>
                        <div><dt className="label">Held constant</dt><dd>{s.constant}</dd></div>
                        <div><dt className="label">Uncertainty</dt><dd>
                          The 95% {boot ? "bootstrap" : "clustered"} interval runs from {f3(e.lo)} to {f3(e.hi)}{crosses ? ", which includes zero: the data are consistent with no link as well as a link in either direction." : ", which does not include zero."}
                          {" "}It is {width > Math.abs(e.coef) * 2 ? "wide relative to the estimate itself" : "narrow relative to the estimate"}.
                          {boot && crosses !== tCrosses && ` The clustered interval (${f3(e.tLo)} to ${f3(e.tHi)}) ${tCrosses ? "includes" : "excludes"} zero, so the two methods disagree; treat this one with care.`}
                          {boot && crosses === tCrosses && Number.isFinite(e.p) && (e.p < 0.05) !== (e.pWild < 0.05) && " The clustered and bootstrap p-values fall on different sides of 0.05, so treat this one with care."}
                        </dd></div>
                        <div><dt className="label">Cannot establish</dt><dd>That money causes results. {s.id === "pooled" ? "Rich teams may also be well run for reasons unrelated to money." : "Changes in a team's money may follow from earlier success, or coincide with other changes inside the team."}</dd></div>
                      </dl>
                    </article>
                  );
                })}
              </div>
            </div>

            <ChartFrame
              meta={{
                id: "LAB-2", dataset: rob.entry, methodology: "robustness",
                title: `Does the two-way estimate survive? ${mLabel}, ${outcome === "points_share" ? "points share" : "position"}`,
                caption: "The same team-and-season model under different samples, measures and controls. If the dots stay near the first one and on the same side of zero, the result does not depend on that choice. Lines are bootstrap intervals where computed, otherwise clustered intervals with t(G − 1).",
                source: "robustness_checks dataset.",
                shows: "How much each check moves the main estimate, with its 95% interval.",
                doesNotShow: "Checks in other units (reverse direction, normalised position; see the note below) and the real-terms check, which cannot change this model because season effects absorb inflation common to all teams.",
                summary: checks.rows.map((r) => `${r.check}: ${f3(n(r.coef))}.`).join(" ") + (checks.loo.length ? ` Leaving out one team at a time gives estimates from ${f3(Math.min(...checks.loo.map((r) => n(r.coef))))} to ${f3(Math.max(...checks.loo.map((r) => n(r.coef))))}.` : ""),
              }}
              table={<DataTable rows={checks.rows} columns={["check", "coef", "ci_t_low", "ci_t_high", "p_t", "ci_boot_low", "ci_boot_high", "p_wild", "n_obs", "n_teams", "note"]} specs={rob.entry?.columns} />}>
              <Plot ariaLabel="Robustness of the two-way estimate" height={Math.max(220, (narrow ? 64 : 46) * (checks.rows.length + (checks.loo.length ? 1 : 0)) + 60)}
                data={[
                  {
                    type: "scatter", mode: "markers", orientation: "h",
                    x: checks.rows.map((r) => n(r.coef)), y: checks.rows.map((r) => wrap(String(r.check), narrow ? 16 : 44)),
                    error_x: { type: "data", symmetric: false, array: checks.rows.map((r) => n(r.plot_high) - n(r.coef)), arrayminus: checks.rows.map((r) => n(r.coef) - n(r.plot_low)), color: SERIES, thickness: 2, width: 0 },
                    marker: { size: 10, color: SERIES }, name: "Estimate", hovertemplate: "<b>%{y}</b><br>coef %{x:.3f}<extra></extra>",
                  },
                  ...(checks.loo.length && outcome === "points_share" ? [{
                    type: "scatter" as const, mode: "lines+markers" as const,
                    x: [Math.min(...checks.loo.map((r) => n(r.coef))), Math.max(...checks.loo.map((r) => n(r.coef)))],
                    y: Array(2).fill(wrap("Leave one team out (range)", narrow ? 16 : 44)),
                    line: { color: ACCENT, width: 4 }, marker: { size: 9, color: ACCENT, symbol: "line-ns-open" as const }, name: "Leave-one-out range",
                    hovertemplate: "range %{x:.3f}<extra></extra>",
                  }] : []),
                ]}
                layout={{
                  margin: { l: 10, r: 16, t: 10, b: 50 }, showlegend: false,
                  xaxis: { title: { text: "coefficient" }, zeroline: false },
                  yaxis: { autorange: "reversed", automargin: true },
                  shapes: [{ type: "line", x0: 0, x1: 0, yref: "paper", y0: 0, y1: 1, line: { color: MUTED, dash: "dash", width: 1 } }],
                }} />
            </ChartFrame>

            {timing?.rev && (
              <Callout title="Which comes first: money or results?">
                Swapping the two variables, this season's {mLabel.toLowerCase()} on last season's points share (same team-and-season model), gives
                a coefficient of {f3(n(timing.rev.coef))} in log points per unit of points share, so a points share one percentage point higher goes
                with {mLabel.toLowerCase()} about {(n(timing.rev.coef)).toFixed(1)}% higher the next season. Clustered p = {fp(n(timing.rev.p_t))} with t(G − 1); bootstrap p = {fp(n(timing.rev.p_wild))}
                {" "}(interval {f3(n(timing.rev.ci_boot_low))} to {f3(n(timing.rev.ci_boot_high))}).
                {" "}{(n(timing.rev.p_t) < 0.05) !== (n(timing.rev.p_wild) < 0.05) ? "The two methods disagree at the 5% level. " : ""}
                Prize money is paid by earlier results, so money following results is expected. This describes timing; it does not show cause and effect.
                {timing.norm && <> With a normalised position (0 = champion, 1 = last) as the outcome, the main model gives {f3(n(timing.norm.coef))} (bootstrap p = {fp(n(timing.norm.p_wild))}).</>}
              </Callout>
            )}

            <Callout title="Testing several things at once">
              Six within-team tests are reported for the main model (three money measures, two outcomes). With that many, one small p-value can turn up by chance. The <b>Holm</b> column adjusts the bootstrap p-values for this. A result that only clears 0.05 before adjustment should be read as suggestive.
            </Callout>

            <Reproduce models={models.entry} rob={rob.entry} />
          </div>
        )}
      </Section>
    </>
  );
}

function EstTable({ ests, outcome }: { ests: Est[]; outcome: string }) {
  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Estimates for each model">
      <table className="w-full text-sm font-mono min-w-[980px]">
        <caption className="sr-only">Estimates for each model</caption>
        <thead><tr className="text-left text-muted">
          {["Model", "Coef.", "SE", "95% CI (clustered)", "p (clustered)", "95% CI (bootstrap)", "p (bootstrap)", "p (Holm)", outcome === "points_share" ? "Per 10% (pp)" : "Places per 10%", "N", "Teams", "R²"].map((h) => <th key={h} scope="col" className="py-2 pr-3 font-normal">{h}</th>)}
        </tr></thead>
        <tbody>
          {ests.map((e) => (
            <tr key={e.spec} className="border-t border-line">
              <th scope="row" className="py-2 pr-3 text-left font-normal text-head">{e.label}</th>
              <td className="pr-3">{f3(e.coef)}</td><td className="pr-3">{f3(e.se)}</td>
              <td className="pr-3 whitespace-nowrap">[{f3(e.tLo)}, {f3(e.tHi)}]</td><td className="pr-3">{fp(e.p)}</td>
              <td className="pr-3 whitespace-nowrap">{Number.isFinite(e.bLo) ? `[${f3(e.bLo)}, ${f3(e.bHi)}]` : "n/a"}</td><td className="pr-3">{fp(e.pWild)}</td>
              <td className="pr-3">{fp(e.pHolm)}</td>
              <td className="pr-3">{Number.isFinite(e.per10) ? e.per10.toFixed(2).replace("-", "−") : "n/a"}</td>
              <td className="pr-3">{e.nObs}</td><td className="pr-3">{e.nTeams}</td><td>{Number.isFinite(e.r2) ? e.r2.toFixed(2) : "n/a"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-muted">Standard errors clustered by team; clustered intervals and p-values use the t distribution with G − 1 degrees of freedom (G = number of teams), not the normal distribution. Bootstrap: restricted wild cluster bootstrap, Webb six-point weights, 9,999 draws, seed 20261119; its interval contains every value the same test does not reject at 5% (Roodman et al. 2019); not computed for the pooled model. Holm: adjusted across the six within-team tests of the two-way model; shown for that model only.</p>
    </div>
  );
}

function Reproduce({ models, rob }: { models?: import("../lib/data").DatasetEntry; rob?: import("../lib/data").DatasetEntry }) {
  return (
    <section aria-labelledby="repro" className="border border-line p-5">
      <h2 id="repro" className="label mb-3">Reproduce these results</h2>
      <dl className="grid md:grid-cols-2 gap-x-8 gap-y-3 text-sm">
        <div><dt className="label">Result files</dt><dd>
          {models && <a className="underline decoration-accent" href={datasetUrl(models, "csv")}>model_results.csv</a>} (version <span className="font-mono">{models?.version}</span>)<br />
          {rob && <a className="underline decoration-accent" href={datasetUrl(rob, "csv")}>robustness_checks.csv</a>} (version <span className="font-mono">{rob?.version}</span>)
        </dd></div>
        <div><dt className="label">Code</dt><dd>
          <a className="underline decoration-accent" href={`${REPO}src/f1moneyball/econometrics/models.py`}>models.py</a> (main models, t(G − 1) and bootstrap intervals) ·{" "}
          <a className="underline decoration-accent" href={`${REPO}src/f1moneyball/econometrics/robustness.py`}>robustness.py</a> (bootstrap, checks, Holm)
        </dd></div>
        <div><dt className="label">Command</dt><dd><code className="font-mono">python -m f1moneyball.pipeline all</code><br /><span className="text-muted">Exact library versions: requirements-lock.txt</span></dd></div>
        <div><dt className="label">Paper</dt><dd><a className="underline decoration-accent" href={import.meta.env.BASE_URL + PAPER}>Working paper</a>, Sections 4 to 6 · <Link className="underline decoration-accent" to="/research/does-money-buy-speed">Research article</Link> · <Link className="underline decoration-accent" to="/faq">Definitions (FAQ)</Link></dd></div>
      </dl>
    </section>
  );
}
