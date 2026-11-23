import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import type { Article, Hypothesis, Reference, ResultBlock, ResultsBasis } from "../../lib/articles";
import { Callout } from "../Ui";
import { BRAND } from "../../lib/brand";
import { useDataset, useStatuses } from "../../lib/data";
import DataTable from "../DataTable";
import { dataReadiness, fmtDate } from "../../lib/status";
import DatasetStatusPanel, { StatusBadge } from "../DatasetStatusPanel";

export const SECTIONS = [
  ["question", "Research question"], ["why", "Why it matters"], ["literature", "Economic intuition and literature"],
  ["hypotheses", "Hypotheses"], ["data", "Data and sources"], ["variables", "Variable definitions"],
  ["strategy", "Empirical strategy"], ["results", "Results"], ["robustness", "Robustness and sensitivity"],
  ["interpretation", "Interpretation"], ["limitations", "Limitations"], ["availability", "Data availability"],
  ["reproducibility", "Reproducibility"], ["references", "References"],
] as const;

export function ArticleSection({ id, n, title, children }: { id: string; n: number; title: string; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="scroll-mt-24 border-t border-line pt-8 mt-10 first:mt-0 first:border-0 first:pt-0">
      <h2 id={`${id}-h`} className="font-serif text-2xl font-semibold text-head flex gap-3 items-baseline">
        <span className="num text-sm text-accent-fg">{String(n).padStart(2, "0")}</span>{title}
      </h2>
      <div className="mt-4 prose-body text-fg">{children}</div>
    </section>
  );
}

export function ArticleHeader({ a }: { a: Article }) {
  return (
    <header className="border-b border-line">
      <div className="mx-auto max-w-6xl px-5 pt-12 pb-10">
        <nav aria-label="Breadcrumb" className="text-xs label"><Link to="/research" className="hover:text-head">Research</Link> / {a.module}</nav>
        <div className="eyebrow mt-5">{BRAND.series}</div>
        <h1 className="font-serif text-4xl md:text-5xl font-semibold tracking-tight text-head mt-3 max-w-3xl">{a.title}</h1>
        <p className="mt-4 font-serif italic text-xl text-muted max-w-2xl leading-relaxed">{a.dek}</p>
      </div>
    </header>
  );
}

export function ArticleMetadata({ a }: { a: Article }) {
  const statuses = useStatuses();
  const ready = dataReadiness(a.datasets, statuses);
  const rows: [string, ReactNode][] = [
    ["Author", a.author],
    ["Series", BRAND.series.replace(/\.$/, "")],
    ["Stage", a.stage],
    ["Published", a.publishedOn ? fmtDate(a.publishedOn) : "Not yet published"],
    ["Text last revised", fmtDate(a.draftRevised)],
    ["Data", ready.label],
    ["Dataset versions", statuses ? a.datasets.map((d) => `${d}: ${statuses[d]?.version ?? "none"}`).join(" · ") : "Status unavailable"],
    ["Methodology", <Link key="m" className="underline decoration-accent" to="/methodology">Methodology</Link>],
    ["Peer review", "Not peer reviewed"],
  ];
  return (
    <dl className="text-xs grid gap-2.5">
      {rows.map(([k, v]) => (
        <div key={k} className="grid grid-cols-[7.5rem_1fr] gap-2"><dt className="label">{k}</dt><dd className="text-fg break-words">{v}</dd></div>
      ))}
    </dl>
  );
}

export function TableOfContents() {
  const go = (id: string) => {
    const el = document.getElementById(id);
    el?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    el?.querySelector("h2")?.setAttribute("tabindex", "-1");
    (el?.querySelector("h2") as HTMLElement | null)?.focus({ preventScroll: true });
  };
  return (
    <nav aria-label="Contents">
      <div className="eyebrow">Contents</div>
      <ol className="mt-3 space-y-1.5 text-sm">
        {SECTIONS.map(([id, label], i) => (
          <li key={id}><button onClick={() => go(id)} className="text-left text-muted hover:text-head"><span className="num text-xs text-accent-fg mr-2">{String(i + 1).padStart(2, "0")}</span>{label}</button></li>
        ))}
      </ol>
    </nav>
  );
}

export function ResearchQuestion({ text }: { text: string }) {
  return <blockquote className="border-l-[3px] border-accent pl-5 font-serif text-2xl leading-snug text-head !max-w-3xl">{text}</blockquote>;
}

export function HypothesisPanel({ items }: { items: Hypothesis[] }) {
  return (
    <div className="border-t-2 border-fg font-sans text-base">
      {items.map((h) => (
        <div key={h.id} className="py-4 border-b border-line grid md:grid-cols-[3rem_1fr_1fr] gap-3">
          <div className="num text-accent-fg">{h.id}</div>
          <p className="!m-0 text-fg">{h.statement}</p>
          <p className="!m-0 text-sm text-muted"><span className="label text-head">Test · </span>{h.test}</p>
        </div>
      ))}
    </div>
  );
}

export function MethodologyPanel({ steps }: { steps: string[] }) {
  return <ol className="list-decimal pl-5 space-y-2 max-w-3xl">{steps.map((s) => <li key={s}>{s}</li>)}</ol>;
}

const KIND_LABEL: Record<ResultBlock["kind"], string> = {
  observed: "Observed result", association: "Statistical association", model_estimate: "Model estimate",
  interpretation: "Interpretation", causal: "Causal conclusion",
};

export function ResultsPanel({ results, datasets, interactive, basis }: { results: ResultBlock[]; datasets: string[]; interactive?: string; basis?: ResultsBasis }) {
  const statuses = useStatuses();
  // Datasets whose live version differs from the one the text was written from.
  const changed = basis && statuses ? Object.entries(basis.versions).filter(([d, v]) => statuses[d] && statuses[d].version !== v).map(([d]) => d) : [];
  if (results.length === 0) {
    return (
      <div className="grid gap-4">
        {datasets.some((d) => statuses?.[d]?.status === "published") ? (
          <p>The written results for this article are not finished. Figures computed from the data published so far are live on the module page{interactive ? <> (<Link className="underline decoration-accent" to={interactive}>open it</Link>)</> : null}; they are labelled there as observations or model estimates. Datasets still missing are listed below.</p>
        ) : (
          <p>No results are published for this article yet. Results will appear here only once they are produced by the pipeline. Datasets still missing are listed below. Each result will be labelled as an observed result, a statistical association, a model estimate, an interpretation or a causal conclusion.</p>
        )}
        {datasets.filter((d) => statuses?.[d]?.status !== "published").map((d) => <DatasetStatusPanel key={d} id={d} compact />)}
      </div>
    );
  }
  return (
    <div className="grid gap-3">
      {basis && (
        <p className="label !normal-case !tracking-normal">
          Figures below were computed from the published data on {fmtDate(basis.date)}
          {" "}(dataset versions: {Object.entries(basis.versions).map(([d, v]) => `${d} ${v}`).join(", ")}).
        </p>
      )}
      {changed.length > 0 && (
        <Callout title="The data have changed since this text was written" tone="caution">
          {changed.join(", ")} {changed.length === 1 ? "has" : "have"} a newer version than the one these results were computed from. The live charts may show different figures until the text is revised.
        </Callout>
      )}
      {results.map((r, i) => (
        <div key={i} className="border-t border-line pt-3">
          <div className="label text-accent-fg">{KIND_LABEL[r.kind]}</div>
          <p className="!mb-0 mt-1">{r.text}</p>
        </div>
      ))}
    </div>
  );
}

export function LimitationsPanel({ items }: { items: string[] }) {
  return (
    <ul className="!list-none !pl-0 grid gap-2">
      {items.map((l) => <li key={l} className="border-l-2 border-accent pl-4 py-1 text-base">{l}</li>)}
    </ul>
  );
}

export function DataAvailability({ datasets, label = "Status of the datasets this article uses" }: { datasets: string[]; label?: string }) {
  const statuses = useStatuses();
  return (
    <div className="overflow-x-auto border-t-2 border-fg font-sans" tabIndex={0} role="region" aria-label={label}>
      <table className="min-w-full text-sm">
        <caption className="sr-only">Status of the datasets this article uses</caption>
        <thead className="border-b border-fg/70 text-left label text-head"><tr><th scope="col" className="p-3">Dataset</th><th scope="col" className="p-3">Status</th><th scope="col" className="p-3">Observations</th><th scope="col" className="p-3">Coverage</th><th scope="col" className="p-3">Version</th></tr></thead>
        <tbody>
          {datasets.map((d) => {
            const s = statuses?.[d];
            return (
              <tr key={d} className="border-t border-line">
                <td className="p-3"><Link className="underline decoration-accent num text-xs" to={`/data?dataset=${d}`}>{d}</Link></td>
                <td className="p-3">{s ? <StatusBadge status={s.status} /> : "n/a"}</td>
                <td className="p-3 num">{s?.observation_count ?? "n/a"}</td>
                <td className="p-3 num">{s?.coverage_start ? `${s.coverage_start}–${s.coverage_end}` : "n/a"}</td>
                <td className="p-3 num text-xs">{s?.version ?? "n/a"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function ReferencesList({ refs }: { refs: Reference[] }) {
  return (
    <ol className="!list-none !pl-0 space-y-3 text-sm">
      {[...refs].sort((a, b) => a.authors.localeCompare(b.authors)).map((r) => (
        <li key={r.title} className="pl-6 -indent-6 leading-relaxed">
          {r.authors} ({r.year}). {r.title}. <em>{r.venue}</em>.
          {r.doi && <> <a className="underline decoration-accent num text-xs" href={`https://doi.org/${r.doi}`} target="_blank" rel="noreferrer">doi:{r.doi}</a></>}
        </li>
      ))}
    </ol>
  );
}

/** Copyable citation. States the real status: no invented publication date, no peer review claim. */
export function HowToCite({ a }: { a: Article }) {
  const [copied, setCopied] = useState("");
  const year = (a.publishedOn ?? a.draftRevised).slice(0, 4);
  const url = typeof window !== "undefined" ? window.location.origin + window.location.pathname : "";
  const [family, given] = [a.author.split(" ").slice(-1)[0], a.author.split(" ")[0]];
  const status = a.publishedOn ? "Not peer reviewed" : `Research design, not peer reviewed; text last revised ${fmtDate(a.draftRevised)}`;
  const apa = `${family}, ${given[0]}. (${year}). ${a.title} [${status}]. ${BRAND.name}: ${BRAND.tagline.replace(/\.$/, "")}. ${url}`;
  const bib = `@misc{${family.toLowerCase()}${year}${a.slug.split("-")[0]},\n  author = {${family}, ${given}},\n  title = {${a.title}},\n  year = {${year}},\n  howpublished = {${BRAND.name}: ${BRAND.tagline.replace(/\.$/, "")}},\n  note = {${status}},\n  url = {${url}}\n}`;
  const copy = (t: string, k: string) => navigator.clipboard?.writeText(t).then(() => { setCopied(k); setTimeout(() => setCopied(""), 2000); });
  return (
    <section aria-labelledby="cite-h" className="mt-12 border-t-2 border-fg pt-4">
      <h2 id="cite-h" className="font-serif text-xl font-semibold text-head">How to cite</h2>
      <p className="mt-2 text-sm text-fg/90 max-w-3xl">{apa}</p>
      <pre className="mt-3 text-xs bg-raise/60 p-3 overflow-x-auto" tabIndex={0} role="region" aria-label="BibTeX citation"><code>{bib}</code></pre>
      <div className="mt-2 flex gap-5 text-sm" aria-live="polite">
        <button className="underline decoration-accent underline-offset-2" onClick={() => copy(apa, "apa")}>{copied === "apa" ? "Copied" : "Copy citation"}</button>
        <button className="underline decoration-accent underline-offset-2" onClick={() => copy(bib, "bib")}>{copied === "bib" ? "Copied" : "Copy BibTeX"}</button>
      </div>
    </section>
  );
}

/** Every robustness estimate for one article, read live from the robustness_checks dataset. */
export function RobustnessTable({ study }: { study: string }) {
  const { status, rows, entry } = useDataset("robustness_checks");
  if (status !== "ready") return null;
  const v = rows.filter((r) => r.study === study);
  if (!v.length) return null;
  return (
    <details className="mt-4 font-sans">
      <summary className="cursor-pointer label !text-accent-fg">Show all {v.length} estimates (robustness_checks dataset)</summary>
      <div className="mt-3">
        <DataTable rows={v} specs={entry?.columns} pageSize={15}
          columns={study === "does-money-buy-speed"
            ? ["check", "metric", "model", "coef", "ci_t_low", "ci_t_high", "p_t", "ci_boot_low", "ci_boot_high", "p_wild", "n_obs", "n_teams", "baseline_coef"]
            : ["check", "metric", "model", "coef", "ci_low", "ci_high", "p_value", "p_wild", "baseline_coef"]} />
      </div>
    </details>
  );
}
