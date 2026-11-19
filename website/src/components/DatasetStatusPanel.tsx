import { Link } from "react-router-dom";
import type { DatasetStatus } from "../lib/data";
import { useStatuses } from "../lib/data";
import { STATUS_LABEL } from "../lib/status";

/** Status as plain text with a shape mark, so it never depends on colour alone. */
export function StatusBadge({ status }: { status: DatasetStatus["status"] }) {
  const published = status === "published";
  return (
    <span className={`inline-flex items-center gap-1.5 text-[0.8rem] whitespace-nowrap ${published ? "text-fg font-semibold" : "text-muted"}`}>
      <span aria-hidden className={published ? "text-timing-green" : ""}>{published ? "●" : "○"}</span>
      {STATUS_LABEL[status]}
    </span>
  );
}

/**
 * Explains why a dataset is not shown. Every word comes from dataset_status.json,
 * which the pipeline builds from config/datasets.yaml. Nothing is hardcoded per page.
 */
export default function DatasetStatusPanel({ id, compact = false, embedded = false }: { id: string; compact?: boolean; embedded?: boolean }) {
  const statuses = useStatuses();
  if (statuses === undefined) return null;
  const s = statuses?.[id];
  if (!s) return <p role="status" className="text-sm text-muted border-t border-line pt-3">Status for <code>{id}</code> is not available. The pipeline has not produced a status file.</p>;
  return (
    <section role="status" aria-label={`${s.dataset_name}: ${STATUS_LABEL[s.status]}`} className="border-l-4 border-accent bg-raise/60 pl-4 pr-4 py-3">
      {!embedded && (
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <span className="font-serif text-lg text-head">{s.dataset_name}</span>
          <StatusBadge status={s.status} />
        </div>
      )}
      {s.status_note && <p className="mt-1 text-sm text-fg">{s.status_note}</p>}
      {!compact && (
        <dl className="mt-3 grid md:grid-cols-3 gap-6 text-sm">
          <div><dt className="label">What it will contain</dt><dd className="mt-1 text-fg/85 leading-relaxed">{s.explanation.would_contain}</dd></div>
          <div><dt className="label">Why it is not shown yet</dt><dd className="mt-1 text-fg/85 leading-relaxed">{s.explanation.why_unavailable}</dd></div>
          <div><dt className="label">Needed before publication</dt><dd className="mt-1 text-fg/85 leading-relaxed">{s.explanation.needed_for_publication}</dd></div>
        </dl>
      )}
      <p className="mt-3 text-xs text-muted">No placeholder values are shown.{!embedded && <> <Link className="underline decoration-accent underline-offset-2" to={`/data?dataset=${id}`}>Dataset profile</Link></>}</p>
    </section>
  );
}
