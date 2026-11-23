import { useEffect, useState } from "react";

export interface ColumnSpec {
  type: string; description: string; unit?: string;
  source?: string; transformation?: string; missing_treatment?: string;
}
export interface SourceRights {
  licence: string; licence_url: string | null; attribution: string | null; restrictions: string | null;
  status: "verified" | "partly verified" | "not verified"; evidence: string | null; checked: string | null;
}
export interface DatasetEntry {
  name: string; title: string; description: string; key: string[]; rows: number;
  columns: Record<string, ColumnSpec>;
  sources: { id: string; name: string; url: string; rights?: SourceRights }[];
  files: { json: string; csv: string };
  coverage?: { season_min: number; season_max: number };
  n_variables?: number; limitations?: string[]; version?: string;
}

export type DatasetStatusValue =
  | "published" | "not_yet_collected" | "under_validation"
  | "insufficient_coverage" | "unavailable_at_source" | "not_comparable";

export interface DatasetStatus {
  dataset_id: string; dataset_name: string; modules: string[]; source_ids: string[];
  status: DatasetStatusValue; status_note: string | null;
  explanation: { would_contain: string; why_unavailable: string; needed_for_publication: string };
  coverage_start: number | null; coverage_end: number | null;
  observation_count: number; variable_count: number;
  missingness: Record<string, { missing: number; share: number | null }>;
  version: string | null; last_updated: string | null;
  validation_status: "passed" | "passed_with_warnings" | "not_run";
  validation_warnings: string[];
}
export interface StatusFile { generated_at_utc: string; datasets: DatasetStatus[] }
export interface QualityIssue { dataset: string; check: string; severity: "error" | "warning"; message: string; n_rows: number }
export interface Manifest {
  project: string; generated_at_utc: string; pipeline_commit: string | null;
  is_synthetic_demo: boolean;
  environment?: { python: string; packages: Record<string, string | null> };
  datasets: Record<string, DatasetEntry>;
  quality: { n_errors: number; n_warnings: number; issues: QualityIssue[] };
}
export type Row = Record<string, string | number | boolean | null>;

const base = import.meta.env.BASE_URL;

let manifestPromise: Promise<Manifest | null> | null = null;
export function loadManifest(): Promise<Manifest | null> {
  manifestPromise ??= fetch(`${base}data/manifest.json`, { cache: "no-cache" })
    .then((r) => (r.ok ? (r.json() as Promise<Manifest>) : null))
    .catch(() => null);
  return manifestPromise;
}

const cache = new Map<string, Promise<Row[]>>();
export function loadDataset(entry: DatasetEntry): Promise<Row[]> {
  if (!cache.has(entry.name)) {
    // The version query string lets browsers cache a dataset until its content changes.
    cache.set(entry.name, fetch(`${base}${entry.files.json}${entry.version ? `?v=${entry.version}` : ""}`)
      .then((r) => r.json())
      .then((d: { columns: string[]; rows: unknown[][] }) =>
        d.rows.map((r) => Object.fromEntries(d.columns.map((c, i) => [c, r[i] as Row[string]])))));
  }
  return cache.get(entry.name)!;
}

export type Status = "loading" | "missing" | "ready";

/** Loads one dataset by name. status = "missing" when the pipeline has not published it. */
export function useDataset(name: string) {
  const [state, setState] = useState<{ status: Status; rows: Row[]; entry?: DatasetEntry; manifest?: Manifest }>(
    { status: "loading", rows: [] });
  useEffect(() => {
    let live = true;
    loadManifest().then(async (m) => {
      const entry = m?.datasets[name];
      if (!m || !entry) { if (live) setState({ status: "missing", rows: [], manifest: m ?? undefined }); return; }
      const rows = await loadDataset(entry);
      if (live) setState({ status: "ready", rows, entry, manifest: m });
    });
    return () => { live = false; };
  }, [name]);
  return state;
}

export function useManifest() {
  const [m, setM] = useState<Manifest | null | undefined>(undefined);
  useEffect(() => { loadManifest().then(setM); }, []);
  return m;
}

export function datasetUrl(entry: DatasetEntry, kind: "csv" | "json") {
  return `${base}${entry.files[kind]}${entry.version ? `?v=${entry.version}` : ""}`;
}

let statusPromise: Promise<StatusFile | null> | null = null;
export function loadStatus(): Promise<StatusFile | null> {
  statusPromise ??= fetch(`${base}data/dataset_status.json`, { cache: "no-cache" })
    .then((r) => (r.ok ? (r.json() as Promise<StatusFile>) : null))
    .catch(() => null);
  return statusPromise;
}

/** All dataset statuses, keyed by id. undefined while loading, null if the file is missing. */
export function useStatuses() {
  const [s, setS] = useState<Record<string, DatasetStatus> | null | undefined>(undefined);
  useEffect(() => {
    loadStatus().then((f) => setS(f ? Object.fromEntries(f.datasets.map((d) => [d.dataset_id, d])) : null));
  }, []);
  return s;
}

export interface ChangeEntry { date: string; category: string; title: string; detail: string; datasets?: string[]; automatic: boolean }
export interface Changelog { categories: Record<string, string>; entries: ChangeEntry[] }
export function useChangelog() {
  const [c, setC] = useState<Changelog | null | undefined>(undefined);
  useEffect(() => {
    fetch(`${base}data/changelog.json`, { cache: "no-cache" }).then((r) => (r.ok ? r.json() : null)).then(setC).catch(() => setC(null));
  }, []);
  return c;
}
