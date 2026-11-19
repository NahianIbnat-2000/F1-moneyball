import { useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import type { Data } from "plotly.js";
import ChartFrame from "../components/ChartFrame";
import DataTable from "../components/DataTable";
import DatasetStatusPanel from "../components/DatasetStatusPanel";
import FinancialClassification from "../components/FinancialClassification";
import Plot from "../components/Plot";
import { Callout, PageHeader, Section } from "../components/Ui";
import { useDataset, type DatasetEntry, type Row } from "../lib/data";
import { BAR_PATTERN_ESTIMATE, BG, GOLD, MUTED, SYMBOL } from "../lib/chartTheme";
import { TEAM_COLOR, teamHex } from "../lib/teams";

// ---------------------------------------------------------------- helpers
const num = (v: Row[string]) => (typeof v === "number" ? v : null);
const pct = (v: number | null, d = 1) => (v === null ? "n/a" : `${(v * 100).toFixed(d)}%`);
const uniq = <T,>(xs: T[]) => [...new Set(xs)];
const seasonsOf = (rows: Row[]) => uniq(rows.map((r) => r.season as number)).sort((a, b) => a - b);
const fieldCls = "border-0 border-b border-fg/60 bg-transparent px-1 py-1 text-sm text-fg";

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <label className="label grid gap-1">{label}
      <select className={fieldCls} value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </label>
  );
}

const METRIC_LABEL: Record<string, string> = {
  operating_costs: "Operating costs", revenue: "Revenue", turnover: "Turnover", staff_costs: "Staff costs",
  estimated_budget: "Estimated budget", sponsorship_revenue: "Sponsorship revenue", headcount: "Headcount",
  operating_profit: "Operating profit", profit_before_tax: "Profit before tax",
};
const mLabel = (m: string) => METRIC_LABEL[m] ?? m;
// Money measures first, headcount last; the first one is the default selection.
const METRIC_ORDER = ["turnover", "revenue", "operating_costs", "staff_costs", "estimated_budget", "sponsorship_revenue", "headcount"];
const byOrder = (a: string, b: string) => (METRIC_ORDER.indexOf(a) + 1 || 99) - (METRIC_ORDER.indexOf(b) + 1 || 99);
// Headcount is a count of people (currency "persons"), not money: no scaling to millions.
const isMoney = (ccy: string) => ccy !== "persons";
const scaleOf = (ccy: string) => (isMoney(ccy) ? 1e6 : 1);
const unitOf = (ccy: string) => (isMoney(ccy) ? `${ccy} millions` : "employees, average for the year");
const fmtVal = (v: number, ccy: string) => (isMoney(ccy) ? `${(v / 1e6).toFixed(1)}M ${ccy}` : `${Math.round(v).toLocaleString("en-US")} employees`);

// ---------------------------------------------------------------- A. resources vs performance
function useFinancialControls(rows: Row[]) {
  const metrics = uniq(rows.map((r) => String(r.metric))).sort(byOrder);
  const [metric, setMetric] = useState(metrics[0] ?? "");
  const currencies = uniq(rows.filter((r) => r.metric === metric).map((r) => String(r.currency)));
  const [currency, setCurrency] = useState(currencies[0] ?? "");
  const ccy = currencies.includes(currency) ? currency : currencies[0] ?? "";
  const seasons = seasonsOf(rows.filter((r) => r.metric === metric && r.currency === ccy));
  const [season, setSeason] = useState("all");
  const controls = (
    <>
      <Select label="Financial measure" value={metric} onChange={setMetric} options={metrics.map((m) => [m, mLabel(m)])} />
      <Select label="Currency / unit" value={ccy} onChange={setCurrency} options={currencies.map((c) => [c, c])} />
      <Select label="Season" value={season} onChange={setSeason} options={[["all", "All seasons"], ...seasons.map((s): [string, string] => [String(s), String(s)])]} />
    </>
  );
  // Rows with both a figure and a sporting record; multi-entity rows are never plotted.
  const view = rows.filter((r) => r.metric === metric && r.currency === ccy && (season === "all" || String(r.season) === season)
    && num(r.value) !== null && num(r.points) !== null && !String(r.exclusion_reason ?? "").startsWith("More than one"));
  return { metric, ccy, season, controls, view };
}

function scatterTraces(view: Row[], y: (r: Row) => number, labels: boolean, ccy: string) {
  return (["reported", "estimate"] as const).map((kind): Data => {
    const rs = view.filter((r) => (kind === "reported") === Boolean(r.is_reported));
    return {
      type: "scatter", mode: labels ? "text+markers" : "markers", name: kind === "reported" ? "Reported figure (audited or official)" : "Estimate",
      x: rs.map((r) => (r.value as number) / scaleOf(ccy)), y: rs.map(y),
      text: rs.map((r) => `${r.team_name ?? r.team_id} ${String(r.season).slice(2)}`), textposition: "top center",
      textfont: { size: 10, color: MUTED },
      marker: { symbol: SYMBOL[kind], size: 10, color: rs.map((r) => teamHex(String(r.team_id))), line: { width: kind === "estimate" ? 2 : 1, color: kind === "estimate" ? rs.map((r) => teamHex(String(r.team_id))) : BG } },
      hovertemplate: isMoney(ccy) ? "<b>%{text}</b><br>%{x:,.1f}M<br>%{y}<extra></extra>" : "<b>%{text}</b><br>%{x:,} employees<br>%{y}<extra></extra>",
    };
  }).filter((t) => (t as { x: number[] }).x.length > 0);
}

function ResourcesVsPerformance({ rows, entry }: { rows: Row[]; entry?: DatasetEntry }) {
  const c = useFinancialControls(rows);
  const [outcome, setOutcome] = useState<"points_share" | "position">("points_share");
  const y = (r: Row) => (outcome === "points_share" ? (r.points_share as number) * 100 : (r.position as number));
  const est = c.view.some((r) => !r.is_reported);
  const top = [...c.view].sort((a, b) => (b.value as number) - (a.value as number))[0];
  return (
    <ChartFrame
      meta={{
        id: outcome === "points_share" ? "MB-1" : "MB-2", dataset: entry, methodology: "financial measures",
        title: `${mLabel(c.metric)} and ${outcome === "points_share" ? "share of championship points" : "championship position"}`,
        caption: "If money buys speed, teams further right should sit higher. Each point is one team in one season, measured with one financial measure only.",
        source: "efficiency dataset: statutory accounts entered by hand (financial_observation) joined to Jolpica-F1 standings.",
        shows: `${mLabel(c.metric)} in ${unitOf(c.ccy)}${isMoney(c.ccy) ? " (original currency, not inflation-adjusted)" : ""} against ${outcome === "points_share" ? "points share of the whole grid" : "final position"}.`,
        doesNotShow: "Whether spending causes results. Success also raises income, so the link can run both ways.",
        estimateWarning: est ? "Hollow markers are estimates, not reported figures." : undefined,
        summary: top ? `${c.view.length} team-seasons shown. The largest figure is ${top.team_name} in ${top.season} (${fmtVal(top.value as number, c.ccy)}), which finished P${top.position} with ${pct(num(top.points_share))} of points.` : "No rows match the selection.",
      }}
      controls={<>{c.controls}<Select label="Outcome" value={outcome} onChange={(v) => setOutcome(v as typeof outcome)} options={[["points_share", "Points share"], ["position", "Championship position"]]} /></>}
      table={<DataTable rows={c.view} columns={["season", "team_name", "entity_name", "value", "currency", "source_class", "points_share", "position"]} specs={entry?.columns} />}>
      <Plot ariaLabel={`Scatter of ${mLabel(c.metric)} against ${outcome}`} height={440} data={scatterTraces(c.view, y, c.season !== "all", c.ccy)}
        layout={{ showlegend: true, legend: { orientation: "h", y: -0.2 },
          xaxis: { title: { text: `${mLabel(c.metric)} (${unitOf(c.ccy)}, log scale)` }, type: "log" },
          yaxis: { title: { text: outcome === "points_share" ? "Share of all constructor points (%)" : "Championship position" }, autorange: outcome === "position" ? "reversed" : true } }} />
    </ChartFrame>
  );
}

function SeasonScatter({ rows, entry, id, title, caption, x, y, xTitle, yTitle, shows, doesNot, summary }: {
  rows: Row[]; entry?: DatasetEntry; id: string; title: string; caption: string; x: string; y: string; xTitle: string; yTitle: string;
  shows: string; doesNot: string; summary: (v: Row[]) => string;
}) {
  const seasons = seasonsOf(rows);
  const [season, setSeason] = useState(String(seasons.at(-1) ?? ""));
  const v = rows.filter((r) => String(r.season) === season && num(r[x]) !== null && num(r[y]) !== null);
  const sx = x.endsWith("rate") || x.endsWith("share") ? 100 : 1;
  const sy = y.endsWith("rate") || y.endsWith("share") ? 100 : 1;
  return (
    <ChartFrame
      meta={{ id, title, caption, dataset: entry, source: "constructor_season dataset (Jolpica-F1 results, qualifying and standings).", shows, doesNotShow: doesNot, summary: summary(v) }}
      controls={<Select label="Season" value={season} onChange={setSeason} options={seasons.map((s) => [String(s), String(s)])} />}
      table={<DataTable rows={v} columns={["team_name", x, y, "points_share", "position"]} specs={entry?.columns} />}>
      <Plot ariaLabel={`${title}, ${season}`} height={400}
        data={[{ type: "scatter", mode: "text+markers", x: v.map((r) => (r[x] as number) * sx), y: v.map((r) => (r[y] as number) * sy),
          text: v.map((r) => String(r.team_name)), textposition: "top center", textfont: { size: 10, color: MUTED },
          marker: { size: 10, color: v.map((r) => teamHex(String(r.team_id))), line: { color: BG, width: 1 } },
          hovertemplate: "<b>%{text}</b><br>%{x:.2f}, %{y:.2f}<extra></extra>" }]}
        layout={{ xaxis: { title: { text: xTitle } }, yaxis: { title: { text: yTitle } } }} />
    </ChartFrame>
  );
}

function Trajectories({ rows, entry }: { rows: Row[]; entry?: DatasetEntry }) {
  const [metric, setMetric] = useState<"points_share" | "position">("points_share");
  const [focus, setFocus] = useState("");
  const teams = useMemo(() => [...new Map(rows.map((r) => [String(r.team_id), String(r.team_name)])).entries()].sort((a, b) => a[1].localeCompare(b[1])), [rows]);
  const traces = useMemo(() => teams.map(([id, name]): Data => {
    const rs = rows.filter((r) => r.team_id === id).sort((a, b) => (a.season as number) - (b.season as number));
    const main = id in TEAM_COLOR;
    return {
      type: "scatter", mode: "lines+markers", name, x: rs.map((r) => r.season as number),
      y: rs.map((r) => (metric === "points_share" ? (r.points_share as number) * 100 : (r.position as number))),
      line: { color: teamHex(id), width: main ? 2 : 1.5 }, marker: { size: 7 }, showlegend: main,
      opacity: focus ? (focus === id ? 1 : 0.12) : main ? 1 : 0.55,
      hovertemplate: `<b>${name}</b><br>%{x}: %{y:.1f}<extra></extra>`,
    };
  }), [rows, teams, metric, focus]);
  return (
    <ChartFrame
      meta={{ id: "MB-3", dataset: entry, methodology: "team lineage", title: "Team performance trajectories",
        caption: "Persistent leaders suggest advantages that build over time, the pattern money could explain. Sudden changes often line up with rule resets.",
        source: "constructor_season dataset (Jolpica-F1 final standings).",
        shows: "Points share or final position of each team lineage per season.", doesNotShow: "Why teams move. Points systems changed, so shares are safer than raw points across eras." }}
      controls={<>
        <Select label="Measure" value={metric} onChange={(v) => setMetric(v as typeof metric)} options={[["points_share", "Points share (%)"], ["position", "Championship position"]]} />
        <Select label="Highlight team" value={focus} onChange={setFocus} options={[["", "None"], ...teams]} />
      </>}>
      <Plot ariaLabel="Line chart of team performance by season" data={traces} height={430}
        layout={{ showlegend: true, legend: { orientation: "h", y: -0.2, font: { size: 11 } },
          yaxis: { title: { text: metric === "points_share" ? "Share of all constructor points (%)" : "Final position" }, autorange: metric === "position" ? "reversed" : true },
          xaxis: { title: { text: "Season" }, dtick: 2 } }} />
    </ChartFrame>
  );
}

// ---------------------------------------------------------------- B. efficiency
function EfficiencyBars({ rows, entry }: { rows: Row[]; entry?: DatasetEntry }) {
  const inc = rows.filter((r) => r.included);
  const c = useFinancialControls(inc);
  const [measureRaw, setMeasure] = useState<"efficiency_ratio" | "points_per_million" | "rank_gap">("efficiency_ratio");
  // Points per million only exists for money measures.
  const measure = measureRaw === "points_per_million" && !isMoney(c.ccy) ? "efficiency_ratio" : measureRaw;
  const seasons = seasonsOf(inc.filter((r) => r.metric === c.metric && r.currency === c.ccy));
  const season = c.season === "all" ? String(seasons.at(-1) ?? "") : c.season;
  const v = inc.filter((r) => r.metric === c.metric && r.currency === c.ccy && String(r.season) === season)
    .sort((a, b) => (b[measure] as number) - (a[measure] as number));
  const excluded = rows.filter((r) => !r.included && r.metric === c.metric && String(r.season) === season);
  const labels: Record<typeof measure, [string, string]> = {
    efficiency_ratio: ["Financial efficiency ratio", "Points share in group / resource share. 1 = points in line with resources"],
    points_per_million: [`Points per million ${c.ccy}`, "Points divided by the financial figure in millions"],
    rank_gap: ["Rank gap", "Resource rank minus points rank. Positive = finished higher than resources rank"],
  };
  const est = v.some((r) => !r.is_reported);
  const best = v[0];
  return (
    <ChartFrame
      meta={{ id: measure === "efficiency_ratio" ? "MB-6" : measure === "points_per_million" ? "MB-7" : "MB-8", dataset: entry, methodology: "financial efficiency",
        title: `${labels[measure][0]}, ${mLabel(c.metric)}, ${season}`,
        caption: "Three separate descriptive measures, shown one at a time rather than combined into a single score. Shares are computed only among teams in the same comparison group.",
        source: "efficiency dataset, computed by src/f1moneyball/econometrics/efficiency.py.",
        shows: labels[measure][1] + `. Group: ${v.length} teams reporting ${mLabel(c.metric)} in ${c.ccy} for ${season}.`,
        doesNotShow: "Technical or production efficiency, and nothing causal. Teams outside the group are not ranked.",
        estimateWarning: est ? "Hatched bars use estimated figures." : undefined,
        summary: best ? `Highest ${labels[measure][0].toLowerCase()} in this group: ${best.team_name} (${(best[measure] as number).toFixed(2)}). ${excluded.length ? `${excluded.length} team rows for this season are excluded; see the data table.` : ""}` : "No comparison group for this selection." }}
      controls={<>{c.controls}<Select label="Measure" value={measure} onChange={(v2) => setMeasure(v2 as typeof measure)} options={isMoney(c.ccy) ? [["efficiency_ratio", "Efficiency ratio"], ["points_per_million", "Points per million"], ["rank_gap", "Rank gap"]] : [["efficiency_ratio", "Efficiency ratio"], ["rank_gap", "Rank gap"]]} /></>}
      table={<DataTable rows={[...v, ...excluded]} columns={["team_name", "value", "resource_share", "points_share_in_group", "efficiency_ratio", "points_per_million", "rank_gap", "source_class", "exclusion_reason"]} specs={entry?.columns} />}>
      {v.length ? (
        <Plot ariaLabel={`Bar chart of ${labels[measure][0]} by team`} height={Math.max(260, v.length * 38 + 80)}
          data={[{ type: "bar", orientation: "h", y: v.map((r) => String(r.team_name)), x: v.map((r) => r[measure] as number),
            marker: { color: v.map((r) => teamHex(String(r.team_id))), pattern: { ...BAR_PATTERN_ESTIMATE, shape: v.map((r) => (r.is_reported ? "" : "/")) } },
            hovertemplate: "%{y}: %{x:.2f}<extra></extra>" }]}
          layout={{ margin: { l: 170, r: 24, t: 10, b: 50 }, yaxis: { autorange: "reversed" }, xaxis: { title: { text: labels[measure][0] } },
            shapes: measure === "efficiency_ratio" ? [{ type: "line", x0: 1, x1: 1, yref: "paper", y0: 0, y1: 1, line: { color: GOLD, width: 1.5, dash: "dot" } }] : [] }} />
      ) : <p className="text-sm text-muted py-6">No comparison group meets the coverage rule for this selection.</p>}
    </ChartFrame>
  );
}

function EfficiencyTrajectories({ rows, entry }: { rows: Row[]; entry?: DatasetEntry }) {
  const inc = rows.filter((r) => r.included);
  const c = useFinancialControls(inc);
  const v = inc.filter((r) => r.metric === c.metric && r.currency === c.ccy);
  const teams = uniq(v.map((r) => String(r.team_id)));
  return (
    <ChartFrame
      meta={{ id: "MB-9", dataset: entry, methodology: "financial efficiency", title: `Efficiency ratio over time, ${mLabel(c.metric)}`,
        caption: "Does a team stay efficient, or does the ratio fall as it grows? Gaps mean the team was outside a comparison group that season.",
        source: "efficiency dataset.", shows: "Efficiency ratio per team and season, included rows only.", doesNotShow: "Seasons where the group was too small; those are left as gaps, not filled." }}
      controls={c.controls}>
      <Plot ariaLabel="Line chart of efficiency ratio by season" height={380}
        data={teams.map((t): Data => { const rs = v.filter((r) => r.team_id === t).sort((a, b) => (a.season as number) - (b.season as number));
          return { type: "scatter", mode: "lines+markers", name: String(rs[0].team_name), x: rs.map((r) => r.season as number), y: rs.map((r) => r.efficiency_ratio as number),
            line: { color: teamHex(t), width: 2 }, marker: { size: 7 }, connectgaps: false }; })}
        layout={{ showlegend: true, legend: { orientation: "h", y: -0.2 }, xaxis: { title: { text: "Season" }, dtick: 1 }, yaxis: { title: { text: "Efficiency ratio" } },
          shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 1, y1: 1, line: { color: GOLD, width: 1.5, dash: "dot" } }] }} />
    </ChartFrame>
  );
}

// ---------------------------------------------------------------- pit stop operations
function PitGapTrend({ rows, entry }: { rows: Row[]; entry?: DatasetEntry }) {
  const [focus, setFocus] = useState("");
  const v = rows.filter((r) => num(r.median_pit_gap_s) !== null);
  const teams = useMemo(() => [...new Map(v.map((r) => [String(r.team_id), String(r.team_name)])).entries()].sort((a, b) => a[1].localeCompare(b[1])), [v]);
  const latest = Math.max(...v.map((r) => r.season as number));
  const best = v.filter((r) => r.season === latest).sort((a, b) => (a.median_pit_gap_s as number) - (b.median_pit_gap_s as number))[0];
  return (
    <ChartFrame
      meta={{ id: "MB-12", dataset: entry, methodology: "pit stops", title: "Pit stop gap to the fastest team",
        caption: "How much slower a team's pit stops were than the best team's in the same race. Lower is better; 0 means the team was usually the fastest.",
        source: "constructor_season dataset; stops from the Jolpica-F1 pit stop endpoint (pit_stop dataset).",
        shows: "Per race: the team's median stop minus the fastest team's median, same pit lane. Then the median over the season's races. Stops over 60 s (red flags, repairs) left out.",
        doesNotShow: "The stationary time alone: durations are total pit-lane time. Nor strategy: a slower stop on a better lap can still gain places.",
        summary: best ? `${v.length} team-seasons from 2011. Fastest in ${latest}: ${best.team_name} (${(best.median_pit_gap_s as number).toFixed(2)} s gap).` : undefined }}
      controls={<Select label="Highlight team" value={focus} onChange={setFocus} options={[["", "None"], ...teams]} />}
      table={<DataTable rows={v} columns={["season", "team_name", "median_pit_gap_s", "pit_races", "service_pit_stops"]} specs={entry?.columns} />}>
      <Plot ariaLabel="Line chart of pit stop gap to the fastest team by season" height={400}
        data={teams.map(([id, name]): Data => {
          const rs = v.filter((r) => r.team_id === id).sort((a, b) => (a.season as number) - (b.season as number));
          const main = id in TEAM_COLOR;
          return { type: "scatter", mode: "lines+markers", name, x: rs.map((r) => r.season as number), y: rs.map((r) => r.median_pit_gap_s as number),
            line: { color: teamHex(id), width: main ? 2 : 1.5 }, marker: { size: 6 }, showlegend: main,
            opacity: focus ? (focus === id ? 1 : 0.12) : main ? 1 : 0.5, hovertemplate: `<b>${name}</b><br>%{x}: %{y:.2f} s<extra></extra>` };
        })}
        layout={{ showlegend: true, legend: { orientation: "h", y: -0.2, font: { size: 11 } }, xaxis: { title: { text: "Season" }, dtick: 2 },
          yaxis: { title: { text: "Seconds slower than fastest team" }, rangemode: "tozero" } }} />
    </ChartFrame>
  );
}

function PitVsResources({ cs, eff, entry }: { cs: Row[]; eff: Row[]; entry?: DatasetEntry }) {
  const gap = new Map(cs.filter((r) => num(r.median_pit_gap_s) !== null).map((r) => [`${r.season}|${r.team_id}`, r]));
  const v = eff.filter((r) => r.metric === "turnover" && num(r.value) !== null && gap.has(`${r.season}|${r.team_id}`))
    .map((r): Row => ({ ...r, gap: gap.get(`${r.season}|${r.team_id}`)!.median_pit_gap_s as number }));
  const teams = [...new Set(v.map((r) => String(r.team_id)))];
  return (
    <ChartFrame
      meta={{ id: "MB-13", dataset: entry, methodology: "pit stops", title: "Do richer teams run faster pit stops?",
        caption: "A different kind of efficiency: not turning money into points, but turning money into a well-drilled operation.",
        source: "efficiency dataset (turnover from Companies House accounts) joined to constructor_season pit stop gaps.",
        shows: "Team turnover (GBP millions, log scale) against the season's pit stop gap. Each point is one team in one season.",
        doesNotShow: "Causation, or teams without UK accounts (Ferrari, Sauber, Racing Bulls, Haas).",
        summary: `${v.length} team-seasons from ${teams.length} teams.` }}
      table={<DataTable rows={v} columns={["season", "team_name", "value", "gap"]} specs={entry?.columns} />}>
      <Plot ariaLabel="Scatter of turnover against pit stop gap" height={400}
        data={teams.map((t): Data => {
          const rs = v.filter((r) => r.team_id === t);
          return { type: "scatter", mode: "markers", name: String(rs[0].team_name), x: rs.map((r) => (r.value as number) / 1e6), y: rs.map((r) => r.gap as number),
            text: rs.map((r) => String(r.season)), marker: { size: 9, color: teamHex(t), line: { width: 1, color: BG } },
            hovertemplate: `<b>${rs[0].team_name} %{text}</b><br>£%{x:,.0f}M<br>%{y:.2f} s<extra></extra>` };
        })}
        layout={{ showlegend: true, legend: { orientation: "h", y: -0.2 }, xaxis: { title: { text: "Turnover (GBP millions, log scale)" }, type: "log" },
          yaxis: { title: { text: "Pit stop gap to fastest team (s)" }, rangemode: "tozero" } }} />
    </ChartFrame>
  );
}

// ---------------------------------------------------------------- C. comparison tool
function Comparison({ cs, eff }: { cs: Row[]; eff: Row[] | null }) {
  const teams = useMemo(() => [...new Map(cs.map((r) => [String(r.team_id), String(r.team_name)])).entries()].sort((a, b) => a[1].localeCompare(b[1])), [cs]);
  const [picked, setPicked] = useState<string[]>([]);
  const toggle = (id: string) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : p.length < 4 ? [...p, id] : p));
  // Comparable seasons: every selected team raced in them.
  const common = picked.length ? seasonsOf(cs).filter((s) => picked.every((t) => cs.some((r) => r.team_id === t && r.season === s))) : [];
  const avg = (t: string, k: string) => { const xs = cs.filter((r) => r.team_id === t && common.includes(r.season as number)).map((r) => num(r[k])).filter((x): x is number => x !== null); return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null; };
  const fin = (t: string): ReactNode => {
    if (!eff) return "Financial data not yet published";
    const inc = eff.filter((r) => r.team_id === t && r.included && common.includes(r.season as number));
    if (inc.length) { const m = inc.map((r) => r.efficiency_ratio as number).sort((a, b) => a - b); return `${m[Math.floor(m.length / 2)].toFixed(2)} (median of ${inc.length})`; }
    const ex = eff.find((r) => r.team_id === t && !r.included);
    return <span className="text-muted">{ex ? `Not comparable: ${ex.exclusion_reason}` : "No figures entered for this team"}</span>;
  };
  const rowsDef: [string, (t: string) => ReactNode][] = [
    ["Mean points share", (t) => pct(avg(t, "points_share"))],
    ["Mean championship position", (t) => avg(t, "position")?.toFixed(1) ?? "n/a"],
    ["Wins (total)", (t) => cs.filter((r) => r.team_id === t && common.includes(r.season as number)).reduce((a, r) => a + ((r.wins as number) || 0), 0)],
    ["Median gap to pole (mean of seasons)", (t) => { const v = avg(t, "median_quali_gap_pct"); return v === null ? "n/a" : `${v.toFixed(2)}%`; }],
    ["Places gained, grid to finish", (t) => avg(t, "mean_grid_to_finish")?.toFixed(2) ?? "n/a"],
    ["Completion rate", (t) => pct(avg(t, "completion_rate"))],
    ["Mechanical retirement rate", (t) => pct(avg(t, "mechanical_dnf_rate"))],
    ["Financial efficiency ratio", fin],
  ];
  return (
    <div className="rule-top pt-3">
      <div className="label text-accent-fg">Figure MB-10</div>
      <h3 className="font-serif text-xl md:text-2xl font-semibold text-head">Constructor comparison</h3>
      <p className="mt-1 font-serif text-fg/80 max-w-3xl">Choose up to four teams. Every measure is averaged over the same seasons, those in which all chosen teams raced, so the comparison uses one definition and one period.</p>
      <fieldset className="mt-4">
        <legend className="label mb-2">Teams ({picked.length} of 4 chosen)</legend>
        <div className="flex flex-wrap gap-x-5 gap-y-2">
          {teams.map(([id, name]) => (
            <label key={id} className={`text-sm flex items-center gap-1.5 ${!picked.includes(id) && picked.length >= 4 ? "opacity-40" : ""}`}>
              <input type="checkbox" checked={picked.includes(id)} disabled={!picked.includes(id) && picked.length >= 4} onChange={() => toggle(id)} />
              <span aria-hidden className="inline-block w-2.5 h-2.5" style={{ background: teamHex(id) }} />{name}
            </label>
          ))}
        </div>
      </fieldset>
      {picked.length > 0 && (
        <div className="mt-5 overflow-x-auto border-t-2 border-fg">
          <table className="min-w-full text-sm">
            <caption className="text-left text-xs text-muted py-2">{common.length ? `Compared over ${common.length} seasons: ${common[0]}–${common.at(-1)}.` : "The chosen teams never raced in the same season."}</caption>
            <thead><tr className="border-b border-fg/70"><th scope="col" className="label text-left py-2 pr-4">Measure</th>{picked.map((t) => <th key={t} scope="col" className="label text-left py-2 pr-4 text-fg">{teams.find(([i]) => i === t)?.[1]}</th>)}</tr></thead>
            <tbody>{rowsDef.map(([label, f]) => (
              <tr key={label} className="border-b border-line"><th scope="row" className="text-left font-normal text-muted py-2 pr-4">{label}</th>{picked.map((t) => <td key={t} className="num py-2 pr-4 align-top">{common.length ? f(t) : "n/a"}</td>)}</tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- D. models
function ModelTable({ rows }: { rows: Row[] }) {
  const f = (v: Row[string], d = 3) => (typeof v === "number" ? v.toFixed(d) : "n/a");
  return (
    <div className="rule-top pt-3">
      <div className="label text-accent-fg">Table MB-11 · Model estimates, not causal effects</div>
      <h3 className="font-serif text-xl md:text-2xl font-semibold text-head">Points share and last season's resources</h3>
      <p className="mt-1 font-serif text-fg/80 max-w-3xl">points_share<sub>it</sub> = β log(resources<sub>i,t−1</sub>) [+ team effects] [+ season effects] + ε<sub>it</sub>. Standard errors clustered by team. The economic size is the change in points share, in percentage points, associated with 10% more resources the season before.</p>
      <div className="mt-4 overflow-x-auto border-t-2 border-fg">
        <table className="min-w-full text-sm">
          <thead><tr className="border-b border-fg/70 text-left">{["Measure", "Specification", "N", "Teams", "β", "SE", "95% CI", "p", "R²", "+10% resources → points share (pp)", "Note"].map((h) => <th key={h} scope="col" className="label py-2 pr-3">{h}</th>)}</tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={String(r.model_id)} className="border-b border-line align-top">
              <td className="py-2 pr-3">{mLabel(String(r.metric))} ({String(r.currency)})</td><td className="py-2 pr-3">{String(r.specification)}</td>
              <td className="num py-2 pr-3">{String(r.n_obs)}</td><td className="num py-2 pr-3">{String(r.n_teams)}</td>
              <td className="num py-2 pr-3">{f(r.coef)}</td><td className="num py-2 pr-3">{f(r.se)}</td>
              <td className="num py-2 pr-3 whitespace-nowrap">{r.estimated ? `[${f(r.ci_low)}, ${f(r.ci_high)}]` : "n/a"}</td>
              <td className="num py-2 pr-3">{f(r.p_value)}</td><td className="num py-2 pr-3">{f(r.r2, 2)}</td><td className="num py-2 pr-3">{f(r.effect_10pct_pp, 2)}</td>
              <td className="py-2 text-xs text-muted min-w-56">{String(r.note)}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- page
const SAFEGUARDS = [
  ["Points systems", "Shares and positions are used instead of raw points, because the fastest-lap point (2019 to 2024) and sprint races (from 2021) changed totals."],
  ["Number of races", "Points per race and shares remove the effect of calendars growing from 19 to 24 races."],
  ["Regulatory change", "Season and regulatory-period effects absorb rule resets such as 2014, 2017 and 2022."],
  ["Entities, not teams", "Financial figures come from legal entities. The reporting company is shown next to every figure."],
  ["Reporting periods", "Each figure keeps its own accounting period and is mapped to a season by a stated rule."],
  ["Currency and inflation", "No conversion yet. Teams in different currencies are never compared directly; figures are nominal."],
  ["Missing figures", "Shown as gaps or listed with a reason. Never filled or imputed."],
  ["Ownership changes", "Team lineages follow the factory through rebrands; robustness checks treat rebrands as new teams."],
];

export default function Moneyball() {
  const cs = useDataset("constructor_season");
  const eff = useDataset("efficiency");
  const models = useDataset("model_results");
  const status = (s: { status: string }, id: string, node: ReactNode) => (s.status === "ready" ? node : s.status === "missing" ? <DatasetStatusPanel id={id} /> : null);
  return (
    <>
      <PageHeader eyebrow="Flagship study · The laboratory" title="F1 Moneyball"
        lede="How efficiently do Formula 1 teams convert financial resources into sporting performance?">
        <p className="mt-4 text-sm text-muted max-w-3xl">The research design, hypotheses, written results and references are in the article. This page holds the live evidence. <Link to="/research/does-money-buy-speed" className="underline decoration-accent underline-offset-2 text-head">Read the article and results</Link></p>
      </PageHeader>

      <Section eyebrow="A" title="Financial resources and sporting performance">
        <div className="grid gap-14">
          {status(eff, "efficiency", <ResourcesVsPerformance rows={eff.rows} entry={eff.entry} />)}
          {status(cs, "constructor_season", <Trajectories rows={cs.rows} entry={cs.entry} />)}
          {cs.status === "ready" && (
            <div className="grid lg:grid-cols-2 gap-10 [&>*]:min-w-0">
              <SeasonScatter rows={cs.rows} entry={cs.entry} id="MB-4" title="Qualifying pace and race-day gains"
                caption="Do teams that qualify slower make it up on Sunday? A team far right but high up gains places through strategy, starts or reliability."
                x="median_quali_gap_pct" y="mean_grid_to_finish" xTitle="Median gap to pole (%)" yTitle="Places gained, grid to finish"
                shows="Each team's median qualifying gap against average places gained by classified cars." doesNot="Driver effects, penalties and safety cars, which also move places."
                summary={(v) => v.length ? `${v.length} teams. Fastest in qualifying: ${[...v].sort((a, b) => (a.median_quali_gap_pct as number) - (b.median_quali_gap_pct as number))[0].team_name}.` : "No data for this season."} />
              <SeasonScatter rows={cs.rows} entry={cs.entry} id="MB-5" title="Reliability and championship performance"
                caption="Reliability is part of operational efficiency: a fast car that does not finish scores nothing."
                x="completion_rate" y="points_share" xTitle="Completion rate (%)" yTitle="Points share (%)"
                shows="Share of car starts classified at the finish against share of points." doesNot="Why cars retired. Mechanical causes are under-recorded from 2024."
                summary={(v) => v.length ? `${v.length} teams. Highest completion rate: ${[...v].sort((a, b) => (b.completion_rate as number) - (a.completion_rate as number))[0].team_name}.` : "No data for this season."} />
            </div>
          )}
        </div>
      </Section>

      <Section eyebrow="B" title="Pit stop operations">
        <div className="grid gap-12">
          {status(cs, "constructor_season", <PitGapTrend rows={cs.rows} entry={cs.entry} />)}
          {cs.status === "ready" && eff.status === "ready" && <PitVsResources cs={cs.rows} eff={eff.rows} entry={eff.entry} />}
        </div>
      </Section>

      <Section eyebrow="C" title="Financial efficiency">
        <div className="grid gap-10">
          <Callout title="What the efficiency ratio is, and is not" tone="caution">
            The ratio compares a team's share of points with its share of resources, among teams that report the same measure in the same currency in the same season (at least four teams). Above 1 means more points than resources would suggest. It is a descriptive comparison, not an estimate of technical efficiency, and it is shown next to two other measures rather than merged into one score.
          </Callout>
          <div><div className="label mb-2">How financial figures are classified</div><FinancialClassification /></div>
          {status(eff, "efficiency", <><EfficiencyBars rows={eff.rows} entry={eff.entry} /><EfficiencyTrajectories rows={eff.rows} entry={eff.entry} /></>)}
        </div>
      </Section>

      <Section eyebrow="D" title="Compare constructors">
        {status(cs, "constructor_season", <Comparison cs={cs.rows} eff={eff.status === "ready" ? eff.rows : null} />)}
      </Section>

      <Section eyebrow="E" title="Model estimates">
        {status(models, "model_results", <ModelTable rows={models.rows} />)}
      </Section>

      <Section eyebrow="F" title="Methodological safeguards">
        <dl className="grid md:grid-cols-2 gap-x-10 border-t-2 border-fg">
          {SAFEGUARDS.map(([k, v]) => <div key={k} className="py-3 border-b border-line"><dt className="font-serif font-semibold text-head">{k}</dt><dd className="text-sm text-fg/85 mt-1">{v}</dd></div>)}
        </dl>
      </Section>
    </>
  );
}
