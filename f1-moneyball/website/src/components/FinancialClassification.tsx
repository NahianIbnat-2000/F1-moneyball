// The five financial-data classifications. One definition, used everywhere.
export const CLASSES: [string, string, string][] = [
  ["audited", "Audited / statutory", "Figure from filed, audited accounts of a legal entity (e.g. UK Companies House). Highest confidence, but the entity may not match the team exactly."],
  ["official_disclosure", "Official disclosure", "Figure published by the team, its parent company or the FIA, without an audit opinion on that figure."],
  ["secondary_estimate", "Secondary estimate", "Estimate from a named press or analyst source. Low confidence. Never shown as if it were reported."],
  ["derived_estimate", "Derived estimate", "Our own calculation from other figures. The method is stated in the transformation field."],
  ["missing", "Missing", "No usable figure. Shown as a gap and never filled."],
];

export default function FinancialClassification() {
  return (
    <dl className="grid sm:grid-cols-2 lg:grid-cols-5 gap-x-6 gap-y-4 text-sm border-t border-fg/70 pt-3">
      {CLASSES.map(([id, label, text]) => (
        <div key={id}>
          <dt className="font-medium text-head">{label}</dt>
          <dd><code className="text-[0.7rem] text-muted">{id}</code></dd>
          <dd className="mt-2 text-xs text-muted leading-relaxed">{text}</dd>
        </div>
      ))}
    </dl>
  );
}
