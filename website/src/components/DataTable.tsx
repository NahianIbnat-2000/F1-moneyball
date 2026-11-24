import { useMemo, useState } from "react";
import type { ColumnSpec, Row } from "../lib/data";

function fmt(v: Row[string], spec?: ColumnSpec) {
  if (v === null || v === undefined || v === "") return <span className="text-muted">n/a</span>;
  if (typeof v === "number") {
    if (spec?.unit === "share") return (v * 100).toFixed(1) + "%";
    if (Math.abs(v) >= 1e6) return v.toLocaleString("en-US");
    return Number.isInteger(v) ? String(v) : v.toFixed(3);
  }
  if (typeof v === "boolean") return v ? "yes" : "no";
  if (typeof v === "string" && v.startsWith("http")) return <a className="underline decoration-accent" href={v} target="_blank" rel="noreferrer">link</a>;
  return String(v);
}

export default function DataTable({ rows, columns, specs, pageSize = 25, onRowClick, selected, caption }: {
  rows: Row[]; columns: string[]; specs?: Record<string, ColumnSpec>; pageSize?: number;
  onRowClick?: (r: Row) => void; selected?: Row | null; caption?: string;
}) {
  const [sort, setSort] = useState<{ col: string; dir: 1 | -1 } | null>(null);
  const [page, setPage] = useState(0);
  const sorted = useMemo(() => {
    if (!sort) return rows;
    return [...rows].sort((a, b) => {
      const x = a[sort.col], y = b[sort.col];
      if (x === y) return 0;
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      return (x > y ? 1 : -1) * sort.dir;
    });
  }, [rows, sort]);
  const pages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const view = sorted.slice(page * pageSize, page * pageSize + pageSize);
  return (
    <div>
      <div className="overflow-x-auto border-t-2 border-fg" tabIndex={0} role="region" aria-label={caption ?? `Table: ${columns.slice(0, 4).join(", ")}${columns.length > 4 ? "…" : ""}`}>
        <table className="min-w-full text-sm">
          {caption && <caption className="sr-only">{caption}</caption>}
          <thead className="border-b border-fg/70">
            <tr>
              {columns.map((c) => (
                <th key={c} scope="col" className="text-left label text-head px-3 py-2 whitespace-nowrap"
                    aria-sort={sort?.col === c ? (sort.dir === 1 ? "ascending" : "descending") : "none"}>
                  <button title={specs?.[c]?.description} onClick={() => { setSort(sort?.col === c ? { col: c, dir: (sort.dir * -1) as 1 | -1 } : { col: c, dir: 1 }); setPage(0); }}>
                    {c}{sort?.col === c ? (sort.dir === 1 ? " ↑" : " ↓") : ""}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {view.map((r, i) => (
              <tr key={i}
                className={`border-t border-line hover:bg-panel/30 ${onRowClick ? "cursor-pointer" : ""} ${selected === r ? "bg-panel/50" : ""}`}
                tabIndex={onRowClick ? 0 : undefined}
                onClick={onRowClick ? () => onRowClick(r) : undefined}
                onKeyDown={onRowClick ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onRowClick(r); } } : undefined}
                aria-selected={onRowClick ? selected === r : undefined}>
                {columns.map((c) => (
                  <td key={c} className={`px-3 py-2 align-top ${typeof r[c] === "number" ? "num text-right" : ""} ${c === "description" ? "min-w-72" : "whitespace-nowrap"}`}>{fmt(r[c], specs?.[c])}</td>
                ))}
              </tr>
            ))}
            {view.length === 0 && <tr><td colSpan={columns.length} className="px-3 py-6 text-center text-muted">No rows match.</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="mt-2 flex justify-between text-xs label">
        <span>{sorted.length} rows</span>
        {pages > 1 && (
          <span className="flex gap-3">
            <button disabled={page === 0} onClick={() => setPage(page - 1)} className="disabled:opacity-30">← prev</button>
            <span>{page + 1} / {pages}</span>
            <button disabled={page >= pages - 1} onClick={() => setPage(page + 1)} className="disabled:opacity-30">next →</button>
          </span>
        )}
      </div>
    </div>
  );
}
