import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Callout, PageHeader, Section } from "../components/Ui";
import { datasetUrl, useDataset, type Row } from "../lib/data";

// Data Provenance Explorer. Every cell is one team-season of the published financial_observation dataset.
// Nothing here is typed by hand except the lineage labels and the order of the rows.

const REPO = "https://github.com/NahianIbnat-2000/F1-moneyball/blob/main/";
const LINEAGES: [string, string][] = [
  ["red_bull", "Red Bull"], ["mercedes", "Mercedes"], ["mclaren", "McLaren"], ["williams", "Williams"],
  ["enstone", "Enstone (Renault, Lotus, Alpine)"], ["silverstone", "Silverstone (Force India, Racing Point, Aston Martin)"],
  ["banbury", "Banbury (Virgin, Marussia, Manor)"], ["leafield", "Leafield (Lotus Racing, Caterham)"],
];
const METRICS: [string, string][] = [
  ["turnover", "Turnover"], ["staff_costs", "Staff costs"], ["headcount", "Headcount"],
  ["operating_profit", "Operating profit"], ["profit_before_tax", "Profit before tax"],
];
const field = "max-w-full min-w-0 border-0 border-b border-fg/60 bg-transparent px-1 py-1.5 text-sm text-fg focus:border-accent";

const str = (v: Row[string]) => (v === null || v === undefined ? "" : String(v));
const isGroup = (r: Row) => str(r.accounting_basis).includes("group");
const days = (a: string, b: string) => Math.round((Date.parse(b) - Date.parse(a)) / 86400000) + 1;
function fmtValue(r: Row) {
  if (r.value === null || r.value === undefined) return "not available";
  const v = Number(r.value);
  if (r.metric === "headcount") return `${v.toLocaleString("en-GB")} people`;
  return `£${(v / 1e6).toLocaleString("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}m`;
}
const localCopy = (notes: string) => notes.match(/Local copy: (\S+?\.pdf)/)?.[1];
const cleanNotes = (notes: string) => notes.replace(/Local copy: \S+\.pdf\.?/, "").trim();

type Cell = { team: string; season: number; rows: Row[] };

export default function Provenance() {
  const { status, rows, entry } = useDataset("financial_observation");
  const [params, setParams] = useSearchParams();
  const metric = params.get("metric") ?? "turnover";
  const flaggedOnly = params.get("flagged") === "1";
  const sel = { team: params.get("team"), season: params.get("season") };
  const set = (patch: Record<string, string | null>) => {
    const p = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) (v === null ? p.delete(k) : p.set(k, v));
    setParams(p, { replace: true, preventScrollReset: true });
  };

  const { seasons, cells, unmapped, counts } = useMemo(() => {
    const mapped = rows.filter((r) => r.season_mapped !== null && r.season_mapped !== undefined && r.season_mapped !== "");
    const ss = [...new Set(mapped.map((r) => Number(r.season_mapped)))].sort((a, b) => a - b);
    const byKey = new Map<string, Cell>();
    for (const r of mapped) {
      const k = `${r.team_id}|${Number(r.season_mapped)}`;
      if (!byKey.has(k)) byKey.set(k, { team: String(r.team_id), season: Number(r.season_mapped), rows: [] });
      byKey.get(k)!.rows.push(r);
    }
    const all = [...byKey.values()];
    const m = (c: Cell) => c.rows.find((r) => r.metric === metric);
    return {
      seasons: ss, cells: byKey,
      unmapped: rows.filter((r) => !mapped.includes(r)),
      counts: {
        withValue: all.filter((c) => { const r = m(c); return r && r.value !== null; }).length,
        group: all.filter((c) => { const r = m(c); return r && r.value !== null && isGroup(r); }).length,
        flagged: all.filter((c) => { const r = m(c); return r && str(r.comparability_warning); }).length,
        // A team-season with a filing record but no figure for this measure counts as "no accounts available".
        missing: all.filter((c) => { const r = m(c); return !r || r.value === null; }).length,
      },
    };
  }, [rows, metric]);

  const selected = sel.team && sel.season ? cells.get(`${sel.team}|${sel.season}`) : undefined;
  const selectedUnmapped = sel.team && sel.season === "unmapped" ? unmapped.filter((r) => r.team_id === sel.team) : [];
  const detailRows = selected?.rows ?? selectedUnmapped;
  const order = new Map(METRICS.map(([k], i) => [k, i]));
  const metricLabel = Object.fromEntries(METRICS);

  return (
    <>
      <PageHeader eyebrow="Data provenance" title="Where every number comes from"
        lede="Each square is one team in one season. Click it to see the filing behind it: the company, the accounting period, the page of the audited accounts, and any warning about comparing it with other years." />

      <Section eyebrow="Coverage" title="Financial data by team and season">
        {status === "loading" && <p className="text-muted">Loading…</p>}
        {status === "missing" && <p className="text-muted">The financial_observation dataset has not been published yet.</p>}
        {status === "ready" && (
          <>
            <div className="flex flex-wrap gap-6 items-end">
              <label className="label grid gap-1 min-w-0 max-w-full">Measure
                <select className={field} value={metric} onChange={(e) => set({ metric: e.target.value === "turnover" ? null : e.target.value })}>
                  {METRICS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="flex items-center gap-2 text-sm text-fg">
                <input type="checkbox" checked={flaggedOnly} onChange={(e) => set({ flagged: e.target.checked ? "1" : null })} />
                Highlight only team-seasons with a comparability warning
              </label>
            </div>

            <dl className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-x-6 border-t-2 border-fg">
              {([["Team-seasons with a value", counts.withValue], ["Group accounts (G)", counts.group],
                ["With a comparability warning (!)", counts.flagged], ["No accounts available (–)", counts.missing]] as [string, number][])
                .map(([k, v]) => <div key={k} className="py-2.5 border-b border-line"><dt className="text-xs text-muted">{k}</dt><dd className="num text-lg text-head mt-0.5">{v}</dd></div>)}
            </dl>

            <div className="mt-6 overflow-x-auto" role="region" aria-label="Coverage grid, scrolls sideways" tabIndex={0}>
              <table className="text-xs num border-collapse">
                <caption className="sr-only">{metricLabel[metric]} coverage by team lineage and season. C company accounts, G group accounts, ! comparability warning, – no accounts available.</caption>
                <thead>
                  <tr>
                    <th scope="col" className="sticky left-0 bg-bg text-left font-normal text-muted pr-3 pb-1">Team lineage</th>
                    {seasons.map((s) => <th key={s} scope="col" className="font-normal text-muted px-0.5 pb-1">{String(s).slice(2)}</th>)}
                    <th scope="col" className="font-normal text-muted px-1 pb-1">Other</th>
                  </tr>
                </thead>
                <tbody>
                  {LINEAGES.map(([tid, name]) => {
                    const extra = unmapped.filter((r) => r.team_id === tid && r.metric === metric);
                    return (
                      <tr key={tid}>
                        <th scope="row" className="sticky left-0 bg-bg text-left font-normal text-fg pr-3 py-0.5 whitespace-nowrap max-w-[6.5rem] sm:max-w-[11rem] overflow-hidden text-ellipsis" title={name}>{name}</th>
                        {seasons.map((s) => {
                          const c = cells.get(`${tid}|${s}`);
                          const r = c?.rows.find((x) => x.metric === metric);
                          if (!c) return <td key={s} className="px-0.5 py-0.5"><span className="block w-7 h-7" aria-hidden="true" /></td>;
                          const has = !!r && r.value !== null && r.value !== undefined;
                          const warn = !!r && !!str(r.comparability_warning);
                          const on = sel.team === tid && sel.season === String(s);
                          const dim = flaggedOnly && !warn;
                          const label = `${name}, ${s}: ${has ? `${fmtValue(r!)}, ${isGroup(r!) ? "group" : "company"} accounts` : "no accounts available"}${warn ? ", comparability warning" : ""}`;
                          return (
                            <td key={s} className="px-0.5 py-0.5">
                              <button type="button" aria-label={label} aria-pressed={on} title={label}
                                onClick={() => set({ team: tid, season: String(s) })}
                                className={`relative block w-7 h-7 rounded-sm border text-[11px] leading-none
                                  ${has ? (isGroup(r!) ? "bg-accent/25 border-accent/60 text-head" : "bg-fg/15 border-fg/30 text-head") : "border-dashed border-fg/40 text-muted"}
                                  ${on ? "outline outline-2 outline-offset-1 outline-head" : ""} ${dim ? "opacity-25" : ""}`}>
                                {has ? (isGroup(r!) ? "G" : "C") : "–"}
                                {warn && <span className="absolute -top-1 -right-1 text-[10px] text-accent-fg font-semibold" aria-hidden="true">!</span>}
                              </button>
                            </td>
                          );
                        })}
                        <td className="px-1 py-0.5">
                          {extra.length > 0 && (
                            <button type="button" onClick={() => set({ team: tid, season: "unmapped" })} aria-pressed={sel.team === tid && sel.season === "unmapped"}
                              className="underline decoration-accent text-[11px] whitespace-nowrap" title="Accounts that cover a period not mapped to any season">
                              {extra.length} stub
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-muted max-w-3xl">
              <b className="text-fg">C</b> company accounts · <b className="text-fg">G</b> group-consolidated accounts · <b className="text-fg">!</b> comparability
              warning · <b className="text-fg">–</b> no full-year accounts available · empty: the team did not race, or files no comparable UK accounts.
              The season is the one the accounting year is mapped to; “stub” accounts cover a short period that is not mapped to any season.
            </p>
          </>
        )}
      </Section>

      {status === "ready" && (
        <Section eyebrow="Source record" title={selected ? `${LINEAGES.find(([t]) => t === selected.team)?.[1]}, ${selected.season}`
          : selectedUnmapped.length ? `${LINEAGES.find(([t]) => t === sel.team)?.[1]}, period not mapped to a season` : "Pick a square above"}>
          {!detailRows.length ? (
            <p className="text-fg max-w-2xl">Click any square in the grid to see the filing, page and accounting details behind that team-season.</p>
          ) : (
            <Detail rows={[...detailRows].sort((a, b) => (order.get(String(a.metric)) ?? 9) - (order.get(String(b.metric)) ?? 9))} metricLabel={metricLabel} />
          )}
        </Section>
      )}

      <Section eyebrow="How this was built">
        <div className="grid md:grid-cols-2 gap-6 max-w-5xl">
          <Callout title="Where the numbers come from">
            <p className="text-sm text-fg">Audited annual accounts filed at UK Companies House. Each figure was read from the filing, checked by hand, and
              recorded with the company number, the page of the PDF and any change made to it (for example £000 to £). A copy of every filing is kept in the
              repository, so a figure can be checked even if the online register changes.</p>
          </Callout>
          <Callout title="What this page does not show" tone="caution">
            <p className="text-sm text-fg">Accounts belong to legal companies, not to teams. Some include other business, and some leave out costs held
              elsewhere in a group. Group and company accounts are not directly comparable, which is why the research checks the results with and without
              this difference (see the <Link className="underline decoration-accent" to="/lab">Econometrics Lab</Link>).</p>
          </Callout>
        </div>
        {entry && (
          <p className="mt-6 text-sm text-fg num">
            Dataset <span className="text-head">financial_observation</span>, version {entry.version ?? "n/a"} ·{" "}
            <a className="underline decoration-accent" href={datasetUrl(entry, "csv")} download>Download CSV</a> ·{" "}
            <Link className="underline decoration-accent" to="/data?dataset=financial_observation">Open in Data Explorer</Link> ·{" "}
            <Link className="underline decoration-accent" to="/methodology">Methodology</Link>
          </p>
        )}
      </Section>
    </>
  );
}

function Detail({ rows, metricLabel }: { rows: Row[]; metricLabel: Record<string, string> }) {
  const r0 = rows[0];
  const start = str(r0.financial_year_start), end = str(r0.financial_year_end);
  const none = rows.every((r) => r.value === null || r.value === undefined);
  const n = start && end ? days(start, end) : null;
  const local = localCopy(str(r0.notes));
  const warnings = [...new Set(rows.map((r) => str(r.comparability_warning)).filter(Boolean))];
  const facts: [string, React.ReactNode][] = [
    ["Company", <>{str(r0.entity_name)} <span className="text-muted">(no. {String(r0.entity_registration).padStart(8, "0")})</span></>],
    ["Accounting period", none ? "No full-year accounts were filed for this season" : start && end ? <>{start} to {end}{n && (n < 350 || n > 380) ? <span className="text-accent-fg"> · {n} days, not a full year</span> : <span className="text-muted"> · {n} days</span>}</> : "n/a"],
    ["Accounts", str(r0.accounting_basis) || "n/a"],
    ["Document", <>{str(r0.document_title) || "n/a"}{str(r0.document_page) && <span className="text-muted"> · {str(r0.document_page)}</span>}</>],
    ["Links", <span className="flex flex-wrap gap-x-4">
      {str(r0.source_url) && <a className="underline decoration-accent" href={str(r0.source_url)} target="_blank" rel="noreferrer">Companies House filing history ↗</a>}
      {local && <a className="underline decoration-accent" href={REPO + local} target="_blank" rel="noreferrer">Saved copy of the filing (PDF) ↗</a>}
    </span>],
    ["Entered by", str(r0.entered_by) || "n/a"],
  ];
  return (
    <div className="grid lg:grid-cols-[3fr_2fr] gap-8">
      <div>
        <dl className="border-t-2 border-fg">
          {facts.map(([k, v]) => <div key={k} className="grid grid-cols-[8rem_1fr] gap-3 py-2 border-b border-line text-sm"><dt className="text-muted">{k}</dt><dd className="text-fg min-w-0 break-words">{v}</dd></div>)}
        </dl>
        {warnings.length > 0 && (
          <div className="mt-5"><Callout title="Comparability warning" tone="caution">{warnings.map((w) => <p key={w} className="text-sm text-fg">{w}</p>)}</Callout></div>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <caption className="sr-only">Figures recorded from this filing</caption>
          <thead><tr className="border-b-2 border-fg text-left"><th className="label py-1.5 pr-3">Measure</th><th className="label py-1.5 pr-3 text-right">Value</th><th className="label py-1.5">How it was recorded</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={str(r.metric)} className="border-b border-line align-top">
                <th scope="row" className="font-normal text-fg py-1.5 pr-3 text-left">{metricLabel[str(r.metric)] ?? str(r.metric)}</th>
                <td className="num text-head py-1.5 pr-3 text-right whitespace-nowrap">{fmtValue(r)}</td>
                <td className="text-xs text-muted py-1.5">
                  {[str(r.transformation), str(r.confidence) && `confidence: ${str(r.confidence)}`, cleanNotes(str(r.notes))].filter(Boolean).join(" · ") || "n/a"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
