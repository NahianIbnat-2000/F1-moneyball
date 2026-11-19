import { BRAND } from "../lib/brand";
import { Callout, PageHeader, Section } from "../components/Ui";

export default function About() {
  return (
    <>
      <PageHeader eyebrow="About" title={BRAND.name} lede={BRAND.positioning} />
      <Section>
        <div className="grid md:grid-cols-[2fr_1fr] gap-10">
          <div className="prose-body">
            <h2 className="font-serif text-2xl font-semibold text-head mt-8 mb-3">Mission</h2>
            <p>F1 Moneyball studies how financial resources, regulation, technology, operational efficiency and commercial strategy shape competitive performance in Formula 1.</p>
            <h2 className="font-serif text-2xl font-semibold text-head mt-8 mb-3">Research philosophy</h2>
            <ul>
              <li>Start from an economic question, not from the data that happens to be available.</li>
              <li>Separate description from causation. Most F1 evidence is descriptive, and we say so.</li>
              <li>Keep audited figures, official disclosures and press estimates apart.</li>
              <li>Publish the code, the data and the limitations together.</li>
            </ul>
            <h2 className="font-serif text-2xl font-semibold text-head mt-8 mb-3">How it is built</h2>
            <p>Python scripts collect and validate the data, compute every statistic and publish small JSON files. This website only reads those files. A GitHub Actions workflow refuses to publish if any validation check fails.</p>
          </div>
          <Callout title="Disclaimer" tone="caution">{BRAND.disclaimer}</Callout>
        </div>
      </Section>
    </>
  );
}
