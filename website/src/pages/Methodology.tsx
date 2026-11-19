import { Link } from "react-router-dom";
import { Callout, PageHeader, Section } from "../components/Ui";
import { useManifest } from "../lib/data";

const SOURCES = [
  ["Jolpica-F1 API", "Race results, qualifying, standings, pit stops", "Automated, cached, 4 req/s and 500 req/h limits respected", "https://github.com/jolpica/jolpica-f1"],
  ["FastF1", "Lap timing, tyre stints, weather (2018+)", "Automated, Phase 2b", "https://docs.fastf1.dev/"],
  ["OpenF1", "Pit-lane times (2023+)", "Robustness source only", "https://openf1.org/"],
  ["UK Companies House", "Audited accounts of UK team entities", "Manual entry with page references, validated in CI", "https://find-and-update.company-information.service.gov.uk/"],
  ["FIA regulations", "Cost cap levels, rule changes", "Manual, each event sourced", "https://www.fia.com/regulation/category/110"],
] as const;

export default function Methodology() {
  const m = useManifest();
  return (
    <>
      <PageHeader eyebrow="Methodology" title="How the evidence is built"
        lede="Raw data, cleaning, features, models and published files are separate stages. Every stage is code in the repository and can be re-run." />
      <Section title="Pipeline">
        <ol className="grid md:grid-cols-6 gap-x-6 text-sm border-t-2 border-fg">
          {["Raw", "Standardize", "Validate", "Features", "Analysis", "Publish"].map((s, i) => (
            <li key={s} className="py-3 border-b border-line md:border-b-0"><div className="num text-xs text-accent-fg">{i + 1}</div><div className="font-medium text-head">{s}</div></li>
          ))}
        </ol>
        <p className="mt-4 text-sm text-muted max-w-3xl leading-relaxed">If any validation check returns an error, the pipeline stops and nothing new is published. Warnings are listed below so that readers see them too.</p>
      </Section>

      <Section title="Data sources">
        <div className="overflow-x-auto border-t-2 border-fg">
          <table className="min-w-full text-sm">
            <thead className="border-b border-fg/70 text-left label text-head"><tr><th className="p-3">Source</th><th className="p-3">Used for</th><th className="p-3">Collection</th></tr></thead>
            <tbody>{SOURCES.map(([n, u, c, url]) => (
              <tr key={n} className="border-t border-line"><td className="p-3"><a href={url} className="underline decoration-accent" target="_blank" rel="noreferrer">{n}</a></td><td className="p-3 text-muted">{u}</td><td className="p-3 text-muted">{c}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </Section>

      <Section title="Key definitions">
        <div className="grid md:grid-cols-2 gap-6 prose-body text-sm">
          <div>
            <h3>Team lineage</h3>
            <p>A team keeps its identity through name changes if the factory and core organisation stay the same (e.g. Force India, Racing Point and Aston Martin at Silverstone). Treating rebrands as new teams is tested as a robustness check.</p>
            <h3>Financial efficiency</h3>
            <p>Points share divided by resource share in the same season, computed only among teams with comparable figures that year. It is a descriptive ratio, not a measure of production efficiency or a causal estimate.</p>
          </div>
          <div>
            <h3>Competitive balance</h3>
            <p>HHI of points shares (normalized for the number of teams), Gini coefficient, coefficient of variation, top-3 share and Spearman rank persistence between consecutive seasons.</p>
            <h3>Mechanical retirements</h3>
            <p>Classified from the race status text. From 2024 many retirements are recorded only as "Retired", so mechanical failures are under-counted in recent seasons. Reliability comparisons across that break are flagged.</p>
          </div>
        </div>
      </Section>

      <Section title="Known limitations">
        <div className="grid md:grid-cols-2 gap-4">
          <Callout title="Financial coverage" tone="caution">Audited accounts exist mainly for UK-registered entities. Ferrari and some other teams do not file comparable accounts, so the financial panel is small and unbalanced.</Callout>
          <Callout title="Entity is not team" tone="caution">Legal entities may include engine work, other businesses or different year-ends. Accounting basis and period are stored with every figure.</Callout>
          <Callout title="Reverse causality" tone="caution">Success raises income and so raises spending. Money-performance models use lagged resources and are reported as associations.</Callout>
          <Callout title="Points systems change" tone="caution">Sprint races (2021+) and the fastest-lap point (2019 to 2024) change totals. Cross-era comparisons use shares and ranks.</Callout>
        </div>
      </Section>

      <Section title="Current data-quality report">
        {m ? (
          <>
            <p className="text-sm text-muted mb-3 num">Built {m.generated_at_utc} · commit {m.pipeline_commit ?? "n/a"} · {m.quality.n_errors} errors · {m.quality.n_warnings} warnings</p>
            <ul className="space-y-2 text-sm">{m.quality.issues.map((i, k) => (
              <li key={k} className="border-b border-line py-2"><span className={`num text-xs mr-2 ${i.severity === "error" ? "text-red-700" : "text-accent-fg"}`}>{i.severity.toUpperCase()}</span><span className="num text-xs text-head mr-2">{i.dataset}</span>{i.message}</li>
            ))}</ul>
          </>
        ) : <p className="text-sm text-muted">No pipeline run published yet.</p>}
      </Section>

      <Section title="Software environment of the current build">
        {m?.environment ? (
          <dl className="grid grid-cols-2 md:grid-cols-4 gap-x-6 border-t-2 border-fg text-sm">
            <div className="py-2 border-b border-line"><dt className="label">python</dt><dd className="num">{m.environment.python}</dd></div>
            {Object.entries(m.environment.packages).map(([k, v]) => <div key={k} className="py-2 border-b border-line"><dt className="label">{k}</dt><dd className="num">{v ?? "not installed"}</dd></div>)}
          </dl>
        ) : <p className="text-sm text-muted">Not recorded yet.</p>}
        <p className="mt-3 text-sm text-muted">Every dataset also carries a content version in the Data Explorer. Changes are listed in the <Link className="underline decoration-accent underline-offset-2" to="/changelog">changelog</Link>. Cite the software with <code>CITATION.cff</code> in the repository.</p>
      </Section>

      <Section title="Reproduce it">
        <pre className="bg-raise text-fg text-xs p-5 overflow-x-auto num border-l-4 border-accent">{`git clone <this repository> && cd f1-moneyball
pip install -e ".[dev]"
python -m f1moneyball.pipeline all     # ingest, build, validate, publish
pytest                                 # test suite
cd website && npm ci && npm run dev    # local site`}</pre>
      </Section>
    </>
  );
}
