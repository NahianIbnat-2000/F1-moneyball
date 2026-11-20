import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import DataTable from "../components/DataTable";
import DatasetStatusPanel, { StatusBadge } from "../components/DatasetStatusPanel";
import FinancialClassification, { CLASSES } from "../components/FinancialClassification";
import { PageHeader, Section } from "../components/Ui";
import { datasetUrl, loadDataset, useManifest, useStatuses, type DatasetEntry, type DatasetStatus, type Row } from "../lib/data";
import { fmtDate } from "../lib/status";

function toCsv(rows: Row[], cols: string[]) {
  const esc = (v: Row[string]) => {
    if (v === null || v === undefined) return "";
    const s = String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [cols.join(","), ...rows.map((r) => cols.map((c) => esc(r[c])).join(","))].join("\n");
}

const field = "border-0 border-b border-fg/60 bg-transparent px-1 py-1.5 text-sm text-fg focus:border-accent";

function Profile({ entry, status }: { entry: DatasetEntry; status: DatasetStatus }) {
  const items: [string, string][] = [
    ["Coverage", status.coverage_start ? `${status.coverage_start}–${status.coverage_end}` : "No season field"],
    ["Observations", status.observation_count.toLocaleString("en-US")],
    ["Variables", String(status.variable_count)],
    ["Last updated", fmtDate(status.last_updated)],
    ["Version", status.version ?? "n/a"],
    ["Validation", status.validation_status.replace(/_/g, " ")],
  ];
  return (
    <div className="grid lg:grid-cols-[2fr_1fr] gap-8">
      <div>
        <p className="text-fg leading-relaxed max-w-2xl">{entry.description}</p>
        <dl className="mt-5 grid grid-cols-2 md:grid-cols-3 gap-x-6 border-t-2 border-fg">
          {items.map(([k, v]) => <div key={k} className="py-2.5 border-b border-line"><dt className="text-xs text-muted">{k}</dt><dd className="num text-sm text-head mt-0.5">{v}</dd></div>)}
        </dl>
        {status.status_note && <p className="mt-3 text-sm text-accent-fg">{status.status_note}</p>}
      </div>
      <div className="grid gap-4 text-sm content-start">
        <div>
          <div className="eyebrow">Sources</div>
          <ul className="mt-1.5 space-y-1">{entry.sources.map((s) => <li key={s.id}><a className="underline decoration-accent" href={s.url} target="_blank" rel="noreferrer">{s.name}</a></li>)}</ul>
        </div>
        <div className="flex gap-4 num text-xs">
          <a className="underline decoration-accent" href={datasetUrl(entry, "csv")} download>Download full CSV</a>
          <a className="underline decoration-accent" href={datasetUrl(entry, "json")}>JSON</a>
        </div>
      </div>
      {(entry.limitations?.length || status.validation_warnings.length) ? (
        <div className="lg:col-span-2 grid md:grid-cols-2 gap-4">
          {!!entry.limitations?.length && (
            <div><div className="eyebrow">Known limitations</div>
              <ul className="mt-2 space-y-1.5 text-sm text-fg">{entry.limitations.map((l) => <li key={l} className="border-l-2 border-accent pl-3">{l}</li>)}</ul></div>
          )}
          {!!status.validation_warnings.length && (
            <div><div className="eyebrow">Validation warnings</div>
              <ul className="mt-2 space-y-1.5 text-sm text-fg">{status.validation_warnings.map((l) => <li key={l} className="border-l-2 border-muted pl-3">{l}</li>)}</ul></div>
          )}
        </div>
      ) : null}
    </div>
  );
}

function Dictionary({ entry, status }: { entry: DatasetEntry; status: DatasetStatus }) {
  return (
    <div className="overflow-x-auto border-t-2 border-fg" tabIndex={0} role="region" aria-label={`Data dictionary for ${entry.title}`}>
      <table className="min-w-full text-sm">
        <caption className="sr-only">Data dictionary for {entry.title}</caption>
        <thead className="border-b border-fg/70 text-left label text-head">
          <tr>{["Variable", "Description", "Unit", "Type", "Source", "Transformation", "Missing values", "Missing"].map((h) => <th key={h} scope="col" className="p-3 whitespace-nowrap">{h}</th>)}</tr>
        </thead>
        <tbody>
          {Object.entries(entry.columns).map(([c, s]) => {
            const m = status.missingness[c];
            return (
              <tr key={c} className="border-t border-line align-top">
                <th scope="row" className="p-3 num text-xs text-head text-left font-normal whitespace-nowrap">{c}</th>
                <td className="p-3 min-w-64">{s.description}</td>
                <td className="p-3 num text-xs">{s.unit ?? ""}</td>
                <td className="p-3 num text-xs">{s.type}</td>
                <td className="p-3 text-xs text-muted min-w-40">{s.source}</td>
                <td className="p-3 text-xs text-muted min-w-48">{s.transformation}</td>
                <td className="p-3 text-xs text-muted min-w-40">{s.missing_treatment}</td>
                <td className="p-3 num text-xs whitespace-nowrap">
                  {m ? (
                    <span className="flex items-center gap-2">
                      <span aria-hidden className="inline-block w-12 h-1.5 bg-raise"><span className="block h-full bg-muted" style={{ width: `${(m.share ?? 0) * 100}%` }} /></span>
                      {m.missing} ({((m.share ?? 0) * 100).toFixed(0)}%)
                    </span>
                  ) : "n/a"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const PROV: [string, string][] = [
  ["entity_name", "Reporting legal entity"], ["entity_registration", "Registration number"], ["team_id", "Sporting team (lineage)"],
  ["metric", "Metric"], ["value", "Original reported figure"], ["currency", "Currency"],
  ["financial_year_start", "Reporting period start"], ["financial_year_end", "Reporting period end"], ["accounting_basis", "Accounting basis"],
  ["source_class", "Classification"], ["confidence", "Confidence"], ["document_title", "Document title"], ["document_page", "Document page"],
  ["source_url", "Source URL"], ["retrieval_date", "Extraction date"], ["transformation", "Transformation applied"],
  ["comparability_warning", "Comparability warning"], ["notes", "Notes"],
];

function Provenance({ row }: { row: Row | null }) {
  if (!row) return <p className="text-sm text-muted">Select a row to see where the figure comes from.</p>;
  const cls = CLASSES.find(([id]) => id === row.source_class);
  return (
    <div className="border-t-2 border-fg pt-3">
      <div className="eyebrow">Provenance</div>
      <p className="mt-2 text-xs text-muted">The legal entity that filed the accounts is not the same thing as the sporting team. Its accounts may include other activities or leave out costs held elsewhere.</p>
      {cls && <p className="mt-2 text-sm"><span className="font-medium text-head">{cls[1]}.</span> <span className="text-muted">{cls[2]}</span></p>}
      <dl className="mt-4 grid gap-2 text-sm">
        {PROV.map(([k, label]) => (
          <div key={k} className="grid grid-cols-[10rem_1fr] gap-2">
            <dt className="text-xs text-muted">{label}</dt>
            <dd className={`break-words ${k === "value" ? "num" : ""}`}>
              {row[k] === null || row[k] === undefined || row[k] === "" ? <span className="text-muted">n/a</span>
                : k === "source_url" ? <a className="underline decoration-accent" href={String(row[k])} target="_blank" rel="noreferrer">Open source document</a>
                : k === "value" ? Number(row[k]).toLocaleString("en-US") : String(row[k])}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export default function DataExplorer() {
  const manifest = useManifest();
  const statuses = useStatuses();
  const [params, setParams] = useSearchParams();
  const ids = statuses ? Object.keys(statuses) : [];
  const id = params.get("dataset") ?? ids.find((d) => statuses?.[d].status === "published") ?? ids[0] ?? "";
  const status = statuses?.[id];
  const entry = manifest?.datasets[id];

  const [tab, setTab] = useState<"data" | "dictionary">("data");
  const [rows, setRows] = useState<Row[]>([]);
  const [q, setQ] = useState("");
  const [team, setTeam] = useState("");
  const [range, setRange] = useState<[number, number] | null>(null);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [picked, setPicked] = useState<Row | null>(null);

  useEffect(() => {
    setRows([]); setQ(""); setTeam(""); setHidden(new Set()); setPicked(null); setRange(null);
    if (!entry) return;
    // Load only the selected dataset, only when it is selected.
    loadDataset(entry).then((r) => {
      setRows(r);
      const s = r.map((x) => x.season ?? x.season_mapped).filter((v): v is number => typeof v === "number");
      setRange(s.length ? [Math.min(...s), Math.max(...s)] : null);
    });
  }, [entry]);

  const allCols = entry ? Object.keys(entry.columns) : [];
  const cols = allCols.filter((c) => !hidden.has(c));
  const seasonCol = allCols.includes("season") ? "season" : allCols.includes("season_mapped") ? "season_mapped" : null;
  const teams = useMemo(() => [...new Set(rows.map((r) => r.team_id).filter(Boolean) as string[])].sort(), [rows]);
  const filtered = useMemo(() => rows.filter((r) => {
    const sv = seasonCol ? r[seasonCol] : null;
    return (!team || r.team_id === team) &&
      (!range || typeof sv !== "number" || (sv >= range[0] && sv <= range[1])) &&
      (!q || Object.values(r).some((v) => String(v ?? "").toLowerCase().includes(q.toLowerCase())));
  }), [rows, team, range, q, seasonCol]);

  const download = () => {
    const blob = new Blob([toCsv(filtered, cols)], { type: "text/csv" });
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: `f1moneyball_${id}_${entry?.version ?? ""}_filtered.csv` });
    a.click(); URL.revokeObjectURL(a.href);
  };
  const isFinancial = id === "financial_observation";

  return (
    <>
      <PageHeader eyebrow="Data Explorer" title="Every dataset, with its status and sources"
        lede="Choose a dataset to see its profile, data dictionary and missing values, then filter and download the exact rows the research uses. Datasets that are not yet published explain why.">
        <p className="mt-4 text-sm text-fg">For the team finances, the <Link className="underline decoration-accent" to="/provenance">provenance explorer</Link> shows the filing and page behind each number.</p>
      </PageHeader>
      <Section>
        {statuses === undefined ? <p className="text-sm text-muted">Loading…</p> : !statuses ? <p className="text-sm text-muted">The pipeline has not produced a status file yet.</p> : (
          <div className="grid grid-cols-1 lg:grid-cols-[16rem_minmax(0,1fr)] gap-8">
            <nav aria-label="Datasets">
              <div className="eyebrow mb-3">Datasets</div>
              <ul className="grid gap-1">
                {ids.map((d) => (
                  <li key={d}>
                    <button onClick={() => { setParams({ dataset: d }); setTab("data"); }} aria-current={d === id ? "true" : undefined}
                      className={`w-full text-left pl-3 py-2 border-l-2 ${d === id ? "border-accent" : "border-transparent hover:border-line"}`}>
                      <div className="text-sm text-head">{statuses[d].dataset_name}</div>
                      <div className="mt-1 flex items-center gap-2"><StatusBadge status={statuses[d].status} />{statuses[d].observation_count > 0 && <span className="num text-xs text-muted">{statuses[d].observation_count}</span>}</div>
                    </button>
                  </li>
                ))}
              </ul>
            </nav>

            <div className="min-w-0">
              {status && (
                <div className="flex flex-wrap items-center gap-3 mb-5">
                  <h2 className="font-serif text-2xl font-semibold text-head">{status.dataset_name}</h2>
                  <StatusBadge status={status.status} />
                  <span className="num text-xs text-muted">{id}</span>
                </div>
              )}

              {!entry || !status ? (
                <div className="grid gap-8">
                  <DatasetStatusPanel id={id} embedded />
                  {isFinancial && <div><div className="eyebrow mb-2">How figures will be classified</div><FinancialClassification /></div>}
                </div>
              ) : (
                <div className="grid gap-8 [&>*]:min-w-0">
                  <Profile entry={entry} status={status} />
                  {isFinancial && <div><div className="eyebrow mb-2">Financial-data classifications</div><FinancialClassification /></div>}

                  <div>
                    <div role="tablist" aria-label="Dataset views" className="flex gap-1 border-b border-line">
                      {(["data", "dictionary"] as const).map((t) => (
                        <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
                          className={`px-4 py-2 text-sm -mb-px border-b-2 ${tab === t ? "border-accent text-head" : "border-transparent text-muted hover:text-head"}`}>
                          {t === "data" ? "Data" : "Dictionary and missing values"}
                        </button>
                      ))}
                    </div>
                    <div role="tabpanel" className="pt-5">
                      {tab === "dictionary" ? <Dictionary entry={entry} status={status} /> : (
                        <>
                          <div className="flex flex-wrap gap-3 items-end mb-4">
                            {range && (
                              <>
                                <label className="text-xs label grid gap-1">From season
                                  <input type="number" className={`${field} w-24`} value={range[0]} max={range[1]} onChange={(e) => setRange([+e.target.value, range[1]])} />
                                </label>
                                <label className="text-xs label grid gap-1">To season
                                  <input type="number" className={`${field} w-24`} value={range[1]} min={range[0]} onChange={(e) => setRange([range[0], +e.target.value])} />
                                </label>
                              </>
                            )}
                            {teams.length > 0 && (
                              <label className="text-xs label grid gap-1">Team
                                <select className={field} value={team} onChange={(e) => setTeam(e.target.value)}>
                                  <option value="">All teams</option>
                                  {teams.map((t) => <option key={t} value={t}>{t}</option>)}
                                </select>
                              </label>
                            )}
                            <label className="text-xs label grid gap-1 flex-1 min-w-40">Search records
                              <input className={field} value={q} placeholder="Any value…" onChange={(e) => setQ(e.target.value)} />
                            </label>
                            <button onClick={download} className="bg-accent text-bg font-semibold text-sm px-4 py-2 hover:bg-accent-fg">Download filtered CSV</button>
                          </div>
                          <details className="mb-4 text-sm">
                            <summary className="cursor-pointer num text-xs text-muted">Choose variables ({cols.length} of {allCols.length})</summary>
                            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
                              {allCols.map((c) => (
                                <label key={c} className="num text-xs flex gap-1 items-center">
                                  <input type="checkbox" checked={!hidden.has(c)} onChange={() => { const h = new Set(hidden); if (h.has(c)) h.delete(c); else h.add(c); setHidden(h); }} />{c}
                                </label>
                              ))}
                            </div>
                          </details>
                          <div className={isFinancial ? "grid xl:grid-cols-[minmax(0,1fr)_22rem] gap-6" : ""}>
                            <DataTable rows={filtered} columns={cols} specs={entry.columns} caption={`${entry.title}, filtered`}
                              onRowClick={isFinancial ? setPicked : undefined} selected={picked} />
                            {isFinancial && <Provenance row={picked} />}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </Section>
    </>
  );
}
