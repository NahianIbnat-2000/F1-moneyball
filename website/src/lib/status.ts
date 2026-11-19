import type { DatasetStatus, DatasetStatusValue } from "./data";

export const STATUS_LABEL: Record<DatasetStatusValue, string> = {
  published: "Published",
  not_yet_collected: "Not yet collected",
  under_validation: "Under validation",
  insufficient_coverage: "Insufficient coverage",
  unavailable_at_source: "Unavailable at source",
  not_comparable: "Not comparable",
};

/** Readiness of an article's data, derived only from dataset_status.json. */
export function dataReadiness(needed: string[], statuses: Record<string, DatasetStatus> | null | undefined) {
  if (!statuses) return { label: "Status unavailable", ready: false, published: 0, total: needed.length };
  const published = needed.filter((d) => statuses[d]?.status === "published").length;
  const label = published === needed.length ? "Data available" : published === 0 ? "Data not yet available" : `Data partly available (${published} of ${needed.length})`;
  return { label, ready: published === needed.length, published, total: needed.length };
}

export const fmtDate = (iso: string | null | undefined) =>
  iso ? new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "Not yet published";
