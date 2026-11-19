import { useState } from "react";
import { Link } from "react-router-dom";
import type { Data } from "plotly.js";
import ChartFrame from "../components/ChartFrame";
import DataTable from "../components/DataTable";
import DatasetStatusPanel from "../components/DatasetStatusPanel";
import Plot from "../components/Plot";
import { Callout, PageHeader, Section } from "../components/Ui";
import { ACCENT, BG, MUTED, SERIES } from "../lib/chartTheme";
import { useDataset, type DatasetEntry, type Row } from "../lib/data";

const LAYERS = [
  ["Gross economic activity", "All spending linked to the event: tickets, hotels, food, transport. What promoters usually report."],
  ["Direct spending", "Spending by visitors who came because of the race."],
  ["Indirect effects", "Further spending by the businesses and workers who received that money."],
  ["Displacement", "Visitors and locals who stayed away, or spent less elsewhere, because of the race."],
  ["Leakage", "Money that leaves the host economy: foreign-owned hotels, hosting fees paid abroad, imported goods."],
  ["Net additional benefit", "Direct and indirect gains minus displacement, leakage and public costs, including what the public money could have done instead."],
];

const fmt = (v: Row[string], d = 1) => (typeof v === "number" ? v.toFixed(d) : "n/a");
const sel = "border-0 border-b border-fg/60 bg-transparent px-1 py-1 text-sm text-fg";

function useHostSeries(rows: Row[]) {
  const keys = [...new Set(rows.map((r) => `${r.region_id}|${r.series}`))];
  const [key, setKey] = useState(keys[0] ?? "");
  const [region, series] = key.split("|");
  const control = keys.length > 1 ? (
    <label className="label grid gap-1">Host and series
      <select className={sel} value={key} onChange={(e) => setKey(e.target.value)}>{keys.map((k) => <option key={k} value={k}>{k.replace("|", " · ")}</option>)}</select>
    </label>
  ) : undefined;
  return { region, series, control, view: rows.filter((r) => r.region_id === region && r.series === series) };
}

function EventStudy({ rows, entry }: { rows: Row[]; entry?: DatasetEntry }) {
  const h = useHostSeries(rows);
  const est = h.view.filter((r) => r.estimated).sort((a, b) => (a.k as number) - (b.k as number));
  const pct = (x: number) => Math.expm1(x) * 100;
  const k0 = est.find((r) => r.k === 0);
  return (
    <ChartFrame
      meta={{ id: "GP-1", dataset: entry, methodology: "race-month event study",
        title: `Race months against the usual season: ${h.region ?? ""}`,
        caption: "If a race brings extra visitors, the race month (0) should sit above the same month in other years. Lower values in the months either side would suggest visitors were moved, not added.",
        source: "gp_event_study dataset, from official monthly series in gp_tourism_monthly.",
        shows: "Approximate % difference from the seasonal pattern and trend, with 95% intervals (HAC standard errors).",
        doesNotShow: "A causal effect. There is no comparison region in this model, and other events can share the race month.",
        summary: k0 ? `Race month: ${fmt(k0.pct_effect)}% [${fmt(pct(k0.ci_low as number))}%, ${fmt(pct(k0.ci_high as number))}%], ${k0.n_races} races, ${k0.n_months} months.` : String(h.view[0]?.note ?? "No estimates.") }}
      controls={h.control}
      table={<DataTable rows={h.view} columns={["k", "coef", "se", "ci_low", "ci_high", "pct_effect", "n_months", "n_races", "note"]} specs={entry?.columns} />}>
      {est.length ? (
        <Plot ariaLabel="Event study: percent difference by month relative to the race" height={340}
          data={[{ type: "bar", x: est.map((r) => r.k as number), y: est.map((r) => pct(r.coef as number)),
            error_y: { type: "data", symmetric: false, array: est.map((r) => pct(r.ci_high as number) - pct(r.coef as number)), arrayminus: est.map((r) => pct(r.coef as number) - pct(r.ci_low as number)), color: MUTED },
            marker: { color: est.map((r) => (r.k === 0 ? ACCENT : SERIES)) }, hovertemplate: "Month %{x}: %{y:.1f}%<extra></extra>" }]}
          layout={{ xaxis: { title: { text: "Months relative to race month" }, tickvals: [-2, -1, 0, 1, 2], ticktext: ["−2", "−1", "Race", "+1", "+2"] },
            yaxis: { title: { text: "Difference from usual (%)" }, zeroline: true } }} />
      ) : <p className="text-sm text-muted py-4">{String(h.view[0]?.note ?? "No estimates.")}</p>}
    </ChartFrame>
  );
}

function ScmPath({ path, inf, pathEntry, infEntry }: { path: Row[]; inf: Row[]; pathEntry?: DatasetEntry; infEntry?: DatasetEntry }) {
  const h = useHostSeries(path);
  const host = inf.find((r) => r.region_id === h.region && r.series === h.series && r.is_host);
  const placebos = inf.filter((r) => r.region_id === h.region && r.series === h.series && r.estimated);
  const v = [...h.view].sort((a, b) => String(a.month).localeCompare(String(b.month)));
  const entryMonth = host?.entry_month ? String(host.entry_month) : undefined;
  const poor = Boolean(host?.poor_pre_fit);
  return (
    <div className="grid gap-12">
      <ChartFrame
        meta={{ id: "GP-2", dataset: pathEntry, methodology: "synthetic control",
          title: `${h.region ?? ""}: observed against synthetic control`,
          caption: "The synthetic line is a weighted mix of comparison regions chosen to track the host before its first race. After entry, the gap between the lines is the estimate of what the race added.",
          source: "gp_scm_path dataset (synthetic control, Abadie, Diamond and Hainmueller 2010).",
          shows: `Log monthly ${h.series}. Weights: ${host?.weights ?? "n/a"}.`,
          doesNotShow: "Spending, jobs or net benefit. Other changes after the race entered the calendar also enter the gap.",
          estimateWarning: poor ? "The pre-entry fit is poor: the gap should not be read as an effect." : undefined,
          summary: host ? `Pre-entry fit (RMSPE) ${fmt(host.rmspe_pre, 3)}; mean post-entry gap ${fmt(host.mean_post_gap_pct)}%; placebo p-value ${fmt(host.p_value, 2)}.` : undefined }}
        controls={h.control}
        table={<DataTable rows={v} columns={["month", "observed", "synthetic", "gap", "period"]} specs={pathEntry?.columns} />}>
        <Plot ariaLabel="Observed and synthetic monthly series" height={380}
          data={[
            { type: "scatter", mode: "lines", name: "Observed host", x: v.map((r) => String(r.month)), y: v.map((r) => r.observed as number), line: { color: ACCENT, width: 2 } },
            { type: "scatter", mode: "lines", name: "Synthetic control", x: v.map((r) => String(r.month)), y: v.map((r) => r.synthetic as number), line: { color: SERIES, width: 2, dash: "dash" } },
          ]}
          layout={{ showlegend: true, legend: { orientation: "h", y: -0.2 }, xaxis: { title: { text: "Month" } }, yaxis: { title: { text: `log ${h.series}` } },
            shapes: entryMonth ? [{ type: "line", xref: "x", yref: "paper", x0: entryMonth, x1: entryMonth, y0: 0, y1: 1, line: { color: MUTED, width: 1.5, dash: "dot" } }] : [] }} />
      </ChartFrame>
      {placebos.length > 1 && (
        <ChartFrame
          meta={{ id: "GP-3", dataset: infEntry, methodology: "placebo inference",
            title: "Is the host's gap unusual? Placebo regions",
            caption: "The same method is run on every comparison region as if it had hosted. If the host's post/pre fit ratio is not among the largest, its gap could be noise.",
            source: "gp_scm_inference dataset.",
            shows: "Ratio of post-entry to pre-entry RMSPE for the host and each placebo region.",
            doesNotShow: "Statistical significance in the usual sense: with few regions, the smallest possible p-value is 1/(regions + 1).",
            summary: host ? `Host ratio ${fmt(host.rmspe_ratio, 2)}; rank-based p-value ${fmt(host.p_value, 2)} from ${placebos.length} units.` : undefined }}
          table={<DataTable rows={placebos} columns={["unit", "is_host", "rmspe_pre", "rmspe_post", "rmspe_ratio", "mean_post_gap_pct", "poor_pre_fit"]} specs={infEntry?.columns} />}>
          <Plot ariaLabel="Bar chart of RMSPE ratios for host and placebo regions" height={Math.max(240, placebos.length * 34 + 80)}
            data={[{ type: "bar", orientation: "h", y: placebos.map((r) => String(r.unit)), x: placebos.map((r) => r.rmspe_ratio as number),
              marker: { color: placebos.map((r) => (r.is_host ? ACCENT : MUTED)), line: { color: BG, width: 1 } }, hovertemplate: "%{y}: %{x:.2f}<extra></extra>" } as Data]}
            layout={{ margin: { l: 120, r: 24, t: 10, b: 50 }, xaxis: { title: { text: "Post / pre RMSPE ratio" } }, yaxis: { categoryorder: "total ascending" } }} />
        </ChartFrame>
      )}
    </div>
  );
}

export default function GrandPrix() {
  const es = useDataset("gp_event_study");
  const path = useDataset("gp_scm_path");
  const inf = useDataset("gp_scm_inference");
  return (
    <>
      <PageHeader eyebrow="Extension module II" title="The Grand Prix Economy"
        lede="Does hosting a Formula 1 Grand Prix generate net additional economic benefits for the host economy?">
        <p className="mt-4 label">Research in progress</p>
        <Link to="/research/grand-prix-economy" className="inline-block mt-3 text-sm underline decoration-accent">Read the research design</Link>
      </PageHeader>

      <Section eyebrow="Sector 1" title="From gross activity to net benefit">
        <div className="grid md:grid-cols-[3fr_2fr] gap-10">
          <ol className="border-l-4 border-accent">
            {LAYERS.map(([t, d], i) => (
              <li key={t} className="pl-5 pb-5">
                <div className="num text-xs text-accent-fg">Layer {i + 1}</div>
                <div className="font-serif uppercase text-xl text-head font-bold">{t}</div>
                <p className="text-sm text-fg/85">{d}</p>
              </li>
            ))}
          </ol>
          <div className="grid gap-5 content-start">
            <Callout title="Why headline figures mislead">Promoters usually report gross activity. It counts spending that would have happened anyway and ignores visitors who avoided the city that week. A rise in visitors during a race weekend does not show that the race caused it.</Callout>
            <Callout title="Case studies, analysed separately" tone="caution"><strong>Singapore</strong> (night race since 2008) and <strong>Austria</strong> (Spielberg, back on the calendar since 2014). Each host is its own research setting; results do not transfer between them. Hosting fees and subsidies are shown only where officially disclosed.</Callout>
          </div>
        </div>
      </Section>

      <Section eyebrow="Sector 2" title="The data">
        <div className="grid gap-5">
          <DatasetStatusPanel id="gp_tourism_monthly" />
          <DatasetStatusPanel id="gp_race_events" compact />
          <p className="text-sm text-muted max-w-3xl">Monthly series are downloaded from official statistics offices and entered with their table references, then validated by the pipeline. The workflow is in <code>docs/GP_DATA_ENTRY.md</code> in the repository.</p>
        </div>
      </Section>

      <Section eyebrow="Sector 3" title="Do race months stand out?">
        {es.status === "ready" ? <EventStudy rows={es.rows} entry={es.entry} /> : es.status === "missing" ? <DatasetStatusPanel id="gp_event_study" /> : null}
      </Section>

      <Section eyebrow="Sector 4" title="What would have happened without the race?">
        {path.status === "ready" && inf.status === "ready" ? <ScmPath path={path.rows} inf={inf.rows} pathEntry={path.entry} infEntry={inf.entry} />
          : path.status === "missing" || inf.status === "missing" ? <DatasetStatusPanel id="gp_scm_path" /> : null}
      </Section>
    </>
  );
}
