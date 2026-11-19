import DatasetStatusPanel from "../components/DatasetStatusPanel";
import { useMemo, useState } from "react";
import type { Data, Shape, Annotation } from "plotly.js";
import ChartFrame from "../components/ChartFrame";
import { ACCENT, ACCENT_FG, BG, MUTED, SERIES } from "../lib/chartTheme";
import DataTable from "../components/DataTable";
import Plot from "../components/Plot";
import { Callout, PageHeader, Section } from "../components/Ui";
import { useDataset, type DatasetEntry, type Row } from "../lib/data";
import { Link } from "react-router-dom";

const MARK = ACCENT;

function CapLevel({ events, entry }: { events: Row[]; entry?: DatasetEntry }) {
  const fin = events.filter((e) => e.category === "financial" && e.value !== null)
    .sort((a, b) => (a.season as number) - (b.season as number));
  const comparable = fin.filter((e) => (e.season as number) <= 2025);
  const later = fin.filter((e) => (e.season as number) > 2025);
  // The 2023 event sets the base level for 2023-2025 (per its description), so the step
  // is held flat to the end of 2025. No value is invented for any season.
  const x = [...comparable.map((e) => e.season as number), 2025];
  const y = [...comparable.map((e) => (e.value as number) / 1e6), (comparable.at(-1)?.value as number) / 1e6];
  const data: Data[] = [
    { type: "scatter", mode: "lines+markers", x, y, line: { shape: "hv", color: SERIES, width: 2 },
      marker: { size: x.map((_, i) => (i === x.length - 1 ? 0 : 9)), color: SERIES, line: { color: BG, width: 2 } },
      hovertemplate: "%{x}: $%{y}M base cap<extra></extra>" },
    { type: "scatter", mode: "markers", x: later.map((e) => e.season as number), y: later.map((e) => (e.value as number) / 1e6),
      marker: { size: 10, color: BG, line: { color: SERIES, width: 2 } },
      hovertemplate: "%{x}: $%{y}M under a wider cost definition<extra></extra>" },
  ];
  const ann: Partial<Annotation>[] = later.map((e) => ({
    x: e.season as number, y: (e.value as number) / 1e6, text: "Wider definition,<br>not comparable", showarrow: true,
    arrowcolor: MARK, ax: -70, ay: 10, font: { size: 11, color: ACCENT_FG },
  }));
  return (
    <ChartFrame
      meta={{
        id: "CC-1", dataset: entry, methodology: "regulation database",
        title: "Cost cap level by season (USD millions)",
        caption: "The financial regulation is the treatment in this module. Its level fell in steps from 2021 to 2023, then rose in 2026 when more costs were brought inside the cap.",
        source: "regulation_event dataset. Seeded from secondary reporting of FIA World Motor Sport Council decisions; primary FIA documents to be verified.",
        shows: "The base cap per season. Adjustments for extra races and inflation (e.g. +3.1% in 2022) are not included.",
        doesNotShow: "How much each team actually spent, or how binding the cap was for each team.",
        estimateWarning: "Values are sourced to secondary reporting and not yet checked against the primary FIA regulations.",
        summary: `${fin.map((e) => `${e.season}: $${(e.value as number) / 1e6}M`).join("; ")}. The 2026 figure uses a wider cost definition and is not comparable with earlier years.`,
      }}
      table={<DataTable rows={fin} columns={["season", "title", "value", "unit", "source_name", "verified_against_primary"]} specs={entry?.columns} />}>
      <Plot ariaLabel="Step chart of the cost cap: 145 million USD in 2021, 140 in 2022, 135 from 2023 to 2025, 215 in 2026 under a wider definition"
        data={data} height={340}
        layout={{ annotations: ann, xaxis: { title: { text: "Season" }, dtick: 1, range: [2020.5, 2026.6] },
          yaxis: { title: { text: "USD millions" }, rangemode: "tozero" } }} />
    </ChartFrame>
  );
}

const INDICATORS: Record<string, [string, string]> = {
  hhi_normalized: ["Normalized HHI", "0 = equal shares, 1 = one team scores everything"],
  gini: ["Gini coefficient", "0 = equal points, higher = more unequal"],
  top3_share: ["Top-3 points share", "Share of all points won by the best three teams"],
  rank_persistence: ["Rank persistence", "Spearman correlation with last season's order"],
  leader_points_share: ["Champion's points share", "Points share of the champion constructor"],
};

function Balance({ rows, events, entry }: { rows: Row[]; events: Row[]; entry?: DatasetEntry }) {
  const [ind, setInd] = useState("hhi_normalized");
  const shapes = useMemo((): Partial<Shape>[] =>
    events.filter((e) => ["FIN-2021-CAP", "TECH-2022-GE"].includes(String(e.event_id))).map((e) => ({
      type: "line", xref: "x", yref: "paper", x0: (e.season as number) - 0.5, x1: (e.season as number) - 0.5, y0: 0, y1: 1,
      line: { color: MARK, width: 1.5, dash: "dot" },
    })), [events]);
  const pts = rows.filter((r) => r[ind] !== null);
  return (
    <ChartFrame
      meta={{
        id: "CC-2", dataset: entry, methodology: "competitive balance",
        title: `${INDICATORS[ind][0]} by season`,
        caption: "If the cost cap compressed the field, concentration should fall after 2021. The dotted lines mark the cap (2021) and the new technical rules (2022), which arrived one year apart.",
        source: "competitive_balance dataset, computed from Jolpica-F1 final constructor standings.",
        shows: INDICATORS[ind][1] + ".",
        doesNotShow: "A causal effect. With every team treated at once and a technical reset in 2022, a before/after change cannot be credited to the cap alone.",
        summary: pts.length ? (() => {
          const pre = pts.filter((r) => (r.season as number) < 2021).map((r) => r[ind] as number);
          const post = pts.filter((r) => (r.season as number) >= 2021).map((r) => r[ind] as number);
          const m = (xs: number[]) => (xs.length ? (xs.reduce((a, b) => a + b, 0) / xs.length).toFixed(3) : "n/a");
          return `Mean ${INDICATORS[ind][0].toLowerCase()}: ${m(pre)} before 2021 (${pre.length} seasons), ${m(post)} from 2021 (${post.length} seasons). Descriptive comparison only.`;
        })() : undefined,
      }}
      table={<DataTable rows={pts} columns={["season", ind, "n_teams", "regulatory_period"]} specs={entry?.columns} />}
      controls={
        <label className="text-xs label">Indicator
          <select className="ml-2 border-0 border-b border-fg/60 bg-transparent px-1 py-1 text-fg" value={ind} onChange={(e) => setInd(e.target.value)}>
            {Object.entries(INDICATORS).map(([k, [l]]) => <option key={k} value={k}>{l}</option>)}
          </select>
        </label>
      }>
      <Plot ariaLabel={`Line chart of ${INDICATORS[ind][0]} by season`} height={360}
        data={[{ type: "scatter", mode: "lines+markers", x: pts.map((r) => r.season as number), y: pts.map((r) => r[ind] as number),
          line: { color: SERIES, width: 2 }, marker: { size: 8, color: SERIES, line: { color: BG, width: 2 } },
          hovertemplate: "%{x}: %{y:.3f}<extra></extra>" }]}
        layout={{ shapes, xaxis: { title: { text: "Season" }, dtick: 2 }, yaxis: { title: { text: INDICATORS[ind][0] } } }} />
    </ChartFrame>
  );
}


const fmt = (v: Row[string], d = 3) => (typeof v === "number" ? v.toFixed(d) : "n/a");

function ItsResults({ rows, entry }: { rows: Row[]; entry?: DatasetEntry }) {
  const its = rows.filter((r) => r.kind === "its" && r.estimated);
  const plac = rows.filter((r) => r.kind === "placebo");
  const [spec, setSpec] = useState("A");
  const view = its.filter((r) => r.specification === spec);
  const inds = view.map((r) => String(r.indicator));
  const label = (k: string) => INDICATORS[k]?.[0] ?? k;
  const data: Data[] = [
    { type: "scatter", mode: "markers", name: "Placebo break years (pre-cap only)", y: plac.filter((r) => inds.includes(String(r.indicator))).map((r) => label(String(r.indicator))),
      x: plac.filter((r) => inds.includes(String(r.indicator))).map((r) => r.level_change as number),
      marker: { symbol: "circle-open", size: 9, color: MUTED }, hovertemplate: "Placebo %{y}: %{x:.3f}<extra></extra>" },
    { type: "scatter", mode: "markers", name: "2021 level change, 95% CI", y: view.map((r) => label(String(r.indicator))), x: view.map((r) => r.level_change as number),
      error_x: { type: "data", symmetric: false, array: view.map((r) => (r.ci_high as number) - (r.level_change as number)), arrayminus: view.map((r) => (r.level_change as number) - (r.ci_low as number)), color: SERIES, thickness: 2 },
      marker: { size: 11, color: SERIES, symbol: "diamond" }, hovertemplate: "%{y}: %{x:.3f}<extra></extra>" },
  ];
  const notEst = rows.filter((r) => r.kind === "its" && !r.estimated);
  return (
    <ChartFrame
      meta={{ id: "CC-3", dataset: entry, methodology: "interrupted time series",
        title: "Change in balance at 2021, against placebo break years",
        caption: "Each diamond is the estimated jump in an indicator at 2021 with its 95% interval. Hollow circles are the same model run on fake break years before the cap. A 2021 change that sits inside the placebo cloud is not unusual.",
        source: "cost_cap_models dataset (src/f1moneyball/econometrics/cost_cap.py), built from competitive_balance.",
        shows: spec === "A" ? "Spec A: level and slope change at 2021, Newey-West standard errors." : "Spec B: adds a 2022 technical-reset dummy, so the 2021 change rests on one season.",
        doesNotShow: "A causal effect of the cap. There is no untreated group, and the 2022 rules arrived one season later.",
        summary: view.length ? view.map((r) => `${label(String(r.indicator))}: ${fmt(r.level_change)} [${fmt(r.ci_low)}, ${fmt(r.ci_high)}]${typeof r.placebo_share_as_large === "number" ? `, ${(r.placebo_share_as_large * 100).toFixed(0)}% of placebos as large` : ""}`).join("; ") + "." : notEst.length ? String(notEst[0].note) : "No estimates." }}
      controls={<label className="label grid gap-1">Specification
        <select className="border-0 border-b border-fg/60 bg-transparent px-1 py-1 text-sm text-fg" value={spec} onChange={(e) => setSpec(e.target.value)}>
          <option value="A">A: level and slope change at 2021</option><option value="B">B: plus 2022 technical-reset term</option>
        </select></label>}
      table={<DataTable rows={[...view, ...notEst]} columns={["indicator", "specification", "n_pre", "n_post", "level_change", "se", "ci_low", "ci_high", "p_value", "slope_change", "tech_level_change", "placebo_share_as_large", "note"]} specs={entry?.columns} />}>
      {view.length ? (
        <Plot ariaLabel="Dot plot of 2021 level changes with confidence intervals and placebo estimates" height={340}
          data={data} layout={{ showlegend: true, legend: { orientation: "h", y: -0.25 }, margin: { l: 190, r: 24, t: 10, b: 60 },
            xaxis: { title: { text: "Level change at the break (indicator units)" }, zeroline: true }, yaxis: { automargin: true } }} />
      ) : <p className="text-sm text-muted py-4">{notEst.length ? String(notEst[0].note) : "No estimates."}</p>}
    </ChartFrame>
  );
}

function DoseResponse({ models, es, esEntry }: { models: Row[]; es: Row[] | null; esEntry?: DatasetEntry }) {
  const did = models.find((r) => r.kind === "dose_response");
  if (!did) return null;
  if (!did.estimated || !es) return <Callout title="Dose-response comparison: not estimated" tone="caution">{String(did.note)}</Callout>;
  const pts = [...es].sort((a, b) => (a.season as number) - (b.season as number));
  return (
    <ChartFrame
      meta={{ id: "CC-4", dataset: esEntry, methodology: "dose-response design",
        title: "Did high spenders lose ground after 2021?",
        caption: "Each point is the season's difference in points share per one standard deviation more pre-cap spending, relative to 2020. Flat points before 2021 support the comparison; a shift after 2021 is consistent with the cap binding on big spenders.",
        source: "cost_cap_event_study dataset; exposure from financial_observation (" + String(did.exposure_measure) + ").",
        shows: `Overall exposure x post estimate: ${fmt(did.level_change)} [${fmt(did.ci_low)}, ${fmt(did.ci_high)}], ${did.n_teams} teams, team and season effects, clustered by team.`,
        doesNotShow: "An effect separable from the 2022 technical rules. Suggestive evidence only.",
        summary: String(did.note) }}
      table={<DataTable rows={pts} columns={["season", "coef", "se", "ci_low", "ci_high", "period", "is_reference"]} specs={esEntry?.columns} />}>
      <Plot ariaLabel="Event study of exposure coefficients by season" height={360}
        data={[{ type: "scatter", mode: "markers", x: pts.map((r) => r.season as number), y: pts.map((r) => r.coef as number),
          error_y: { type: "data", symmetric: false, array: pts.map((r) => (r.ci_high as number) - (r.coef as number)), arrayminus: pts.map((r) => (r.coef as number) - (r.ci_low as number)), color: SERIES, thickness: 1.5 },
          marker: { size: 9, color: pts.map((r) => (r.is_reference ? BG : SERIES)), line: { color: SERIES, width: 2 } }, hovertemplate: "%{x}: %{y:.3f}<extra></extra>" }]}
        layout={{ xaxis: { title: { text: "Season" }, dtick: 1 }, yaxis: { title: { text: "Points share per SD of pre-cap spending" }, zeroline: true },
          shapes: [{ type: "line", xref: "x", yref: "paper", x0: 2020.5, x1: 2020.5, y0: 0, y1: 1, line: { color: MARK, width: 1.5, dash: "dot" } }] }} />
    </ChartFrame>
  );
}

export default function CostCap() {
  const reg = useDataset("regulation_event");
  const bal = useDataset("competitive_balance");
  const ccm = useDataset("cost_cap_models");
  const cces = useDataset("cost_cap_event_study");
  return (
    <>
      <PageHeader eyebrow="Extension module I" title="The Cost Cap Paradox"
        lede="Did the introduction of the Formula 1 cost cap change competitive balance?">
        <p className="mt-4 label">Research in progress</p>
        <Link to="/research/cost-cap-paradox" className="inline-block mt-3 text-sm underline decoration-accent">Read the research design</Link>
      </PageHeader>

      <Section eyebrow="Sector 1" title="The treatment: what changed and when">
        {reg.status === "ready" ? <CapLevel events={reg.rows} entry={reg.entry} /> : reg.status === "missing" ? <DatasetStatusPanel id="regulation_event" /> : null}
      </Section>

      <Section eyebrow="Sector 2" title="Competitive balance over time">
        {bal.status === "ready" ? <Balance rows={bal.rows} events={reg.rows} entry={bal.entry} /> :
          bal.status === "missing" ? <DatasetStatusPanel id="competitive_balance" /> : null}
      </Section>

      <Section eyebrow="Sector 3" title="Did balance change at 2021?">
        {ccm.status === "ready" ? <ItsResults rows={ccm.rows} entry={ccm.entry} /> : ccm.status === "missing" ? <DatasetStatusPanel id="cost_cap_models" /> : null}
      </Section>

      <Section eyebrow="Sector 4" title="Who had to cut most, and what happened to them?">
        {ccm.status === "ready" ? <DoseResponse models={ccm.rows} es={cces.status === "ready" ? cces.rows : null} esEntry={cces.entry} />
          : ccm.status === "missing" ? <DatasetStatusPanel id="cost_cap_event_study" /> : null}
      </Section>

      <Section title="Why causal identification is hard here">
        <div className="grid md:grid-cols-2 gap-6">
          <Callout title="1 · No untreated group">Every team came under the cap in the same season. There is no control team to compare against.</Callout>
          <Callout title="2 · Overlapping changes">The ground-effect technical rules arrived in 2022, one year after the cap. Season-level data cannot separate the two.</Callout>
          <Callout title="3 · COVID-19 disruption">2020 and 2021 had changed calendars, frozen chassis parts and lower revenue, all of which affect the pre-period.</Callout>
          <Callout title="4 · Short post-period">Only five capped seasons with comparable rules (2021 to 2025). Season-level tests have very little power.</Callout>
        </div>
        <div className="mt-6">
          <Callout title="How this module responds" tone="caution">
            Three designs, each labelled with what it can show: an interrupted time series (descriptive), placebo break years (is 2021 unusual?), and a dose-response comparison of teams that had to cut more against teams already near the cap, with an event study to check pre-trends (suggestive). None is reported as the causal effect of the cap.
          </Callout>
        </div>
      </Section>

      <Section title="Regulation database">
        {reg.status === "ready" && reg.entry ? (
          <DataTable rows={reg.rows} specs={reg.entry.columns}
            columns={["season", "category", "title", "value", "unit", "source_name", "source_url", "verified_against_primary"]} />
        ) : null}
      </Section>
    </>
  );
}
