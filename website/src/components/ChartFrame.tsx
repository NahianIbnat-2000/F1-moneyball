import { useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { datasetUrl, type DatasetEntry } from "../lib/data";

export interface ChartMeta {
  /** Stable chart identifier, e.g. "MB-1". Used in citations and the changelog. */
  id: string;
  title: string;
  /** One-sentence explanation of why this chart matters for the research question. */
  caption: string;
  source: string;
  shows: string;
  doesNotShow: string;
  /** Published dataset the chart reads. Supplies coverage, version and the download link. */
  dataset?: DatasetEntry;
  methodology?: string;
  /** Set when any plotted value is an estimate rather than reported. */
  estimateWarning?: string;
  /** Plain-language reading of the chart for readers who cannot see it. Generated from data. */
  summary?: string;
}

/** Every chart: numbered figure, title, controls, plot, notes, source, data table, links. */
export default function ChartFrame({ meta, children, controls, table }: { meta: ChartMeta; children: ReactNode; controls?: ReactNode; table?: ReactNode }) {
  const [showTable, setShowTable] = useState(false);
  const ref = useRef<HTMLElement>(null);
  const download = async (format: "png" | "svg") => {
    const gd = ref.current?.querySelector(".js-plotly-plot");
    if (!gd) return;
    const Plotly = (await import("plotly.js-basic-dist-min")).default;
    Plotly.downloadImage(gd, { format, filename: `f1moneyball_${meta.id}`, width: 1200, height: 700 });
  };
  return (
    <figure ref={ref} className="rule-top pt-3 min-w-0 max-w-full">
      <div className="label text-accent-fg">Figure {meta.id}</div>
      <h3 className="font-serif text-xl md:text-2xl font-semibold text-head mt-0.5">{meta.title}</h3>
      <p className="mt-1 font-serif text-fg/80 max-w-3xl leading-relaxed">{meta.caption}</p>
      {controls && <div className="mt-4 flex flex-wrap gap-4 items-end">{controls}</div>}
      {meta.estimateWarning && <p className="mt-3 text-sm text-accent-fg"><span aria-hidden>△ </span>{meta.estimateWarning}</p>}
      <div className="mt-3">{children}</div>
      {meta.summary && <p className="text-sm text-fg/85 max-w-3xl"><span className="label">Reading the chart · </span>{meta.summary}</p>}
      <figcaption className="mt-3 pt-3 border-t border-line grid gap-3 md:grid-cols-3 text-xs text-muted leading-relaxed">
        <div><span className="font-semibold text-fg">Shows. </span>{meta.shows}</div>
        <div><span className="font-semibold text-fg">Does not show. </span>{meta.doesNotShow}</div>
        <div><span className="font-semibold text-fg">Source. </span>{meta.source}</div>
      </figcaption>
      <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-muted">
        {meta.dataset?.coverage && <span className="num">Seasons {meta.dataset.coverage.season_min}–{meta.dataset.coverage.season_max}</span>}
        {meta.dataset && <span className="num">{meta.dataset.rows} observations · version {meta.dataset.version ?? "n/a"}</span>}
        {meta.dataset && <a className="inline-block py-1.5 underline decoration-accent underline-offset-2" href={datasetUrl(meta.dataset, "csv")} download>Download data (CSV)</a>}
        <button className="inline-block py-1.5 underline decoration-accent underline-offset-2" onClick={() => download("png")}>Download PNG</button>
        <button className="inline-block py-1.5 underline decoration-accent underline-offset-2" onClick={() => download("svg")}>Download SVG</button>
        {table && <button className="inline-block py-1.5 underline decoration-accent underline-offset-2" aria-expanded={showTable} onClick={() => setShowTable(!showTable)}>{showTable ? "Hide" : "Show"} data table</button>}
        <Link className="inline-block py-1.5 underline decoration-accent underline-offset-2" to="/methodology">Methodology{meta.methodology ? `: ${meta.methodology}` : ""}</Link>
      </div>
      {showTable && <div className="mt-3">{table}</div>}
    </figure>
  );
}
