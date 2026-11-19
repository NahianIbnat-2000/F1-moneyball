import { Link } from "react-router-dom";
import { ARTICLES } from "../lib/articles";
import { BRAND } from "../lib/brand";
import { useStatuses } from "../lib/data";
import { dataReadiness, fmtDate } from "../lib/status";
import { PageHeader, Section } from "../components/Ui";

export default function Research() {
  const statuses = useStatuses();
  return (
    <>
      <PageHeader eyebrow="Research" title={BRAND.series.replace(/\.$/, "")}
        lede="Each study follows the same structure: question, motivation, literature, hypotheses, data, strategy, results, robustness, limitations, data availability, reproducibility and references. Results appear only when the pipeline has produced them." />
      <Section>
        <div className="grid gap-6">
          {ARTICLES.map((a) => (
            <article key={a.slug} className={`${a.flagship ? "rule-thick" : "rule-top"} pt-5 pb-4 grid md:grid-cols-[2fr_1fr] gap-6`}>
              <div>
                <div className="flex flex-wrap gap-3 items-center">
                  <span className="eyebrow">{a.flagship ? `Flagship · ${a.module}` : a.module}</span>
                  <span className="text-sm text-muted">{a.stage}</span>
                </div>
                <h2 className="font-serif text-2xl md:text-3xl font-semibold text-head mt-3"><Link to={`/research/${a.slug}`} className="hover:text-accent-fg">{a.title}</Link></h2>
                <p className="mt-2 text-muted leading-relaxed max-w-2xl">{a.question}</p>
                <Link to={`/research/${a.slug}`} className="inline-block mt-4 text-sm underline decoration-accent">Read the study: {a.title}</Link>
              </div>
              <dl className="text-sm grid gap-3 content-start">
                <div><dt className="label text-head">Data</dt><dd className="text-muted">{dataReadiness(a.datasets, statuses).label}</dd></div>
                <div><dt className="label text-head">Published</dt><dd className="text-muted">{a.publishedOn ? fmtDate(a.publishedOn) : "Not yet published"}</dd></div>
                <div><dt className="label text-head">Hypotheses</dt><dd className="text-muted">{a.hypotheses.map((h) => h.id).join(", ")}</dd></div>
              </dl>
            </article>
          ))}
        </div>
      </Section>
    </>
  );
}
