import { useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader, Section } from "../components/Ui";
import { useChangelog } from "../lib/data";
import { fmtDate } from "../lib/status";

export default function Changelog() {
  const c = useChangelog();
  const [cat, setCat] = useState("");
  return (
    <>
      <PageHeader eyebrow="Changelog" title="What changed, and when"
        lede="New and corrected data, methodological changes, revised analysis and new publications are kept apart from routine website changes. Dataset entries are added by the pipeline whenever a dataset's content changes." />
      <Section>
        {c === undefined ? <p className="text-sm text-muted">Loading…</p> : !c ? <p className="text-sm text-muted">No changelog has been published yet.</p> : (
          <>
            <label className="label grid gap-1 max-w-xs mb-6">Show
              <select className="border-0 border-b border-fg/60 bg-transparent px-1 py-1 text-sm text-fg" value={cat} onChange={(e) => setCat(e.target.value)}>
                <option value="">All changes</option>
                {Object.entries(c.categories).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            <ol className="border-t-2 border-fg">
              {c.entries.filter((e) => !cat || e.category === cat).map((e, i) => (
                <li key={i} className="grid md:grid-cols-[9rem_11rem_1fr] gap-x-6 gap-y-1 py-4 border-b border-line">
                  <time className="num text-sm text-muted" dateTime={e.date}>{fmtDate(e.date)}</time>
                  <span className={`text-sm ${e.category === "website" ? "text-muted" : "text-accent-fg font-semibold"}`}>{c.categories[e.category] ?? e.category}{e.automatic ? " · automatic" : ""}</span>
                  <div>
                    <div className="font-serif text-lg text-head">{e.title}</div>
                    <p className="text-sm text-fg/85 mt-0.5 max-w-3xl">{e.detail}</p>
                    {e.datasets?.length ? <p className="text-xs text-muted mt-1">Datasets: {e.datasets.map((d, j) => <span key={d}>{j ? ", " : ""}<Link className="underline decoration-accent underline-offset-2" to={`/data?dataset=${d}`}>{d}</Link></span>)}</p> : null}
                  </div>
                </li>
              ))}
            </ol>
          </>
        )}
      </Section>
    </>
  );
}
