import { NavLink, Outlet, Link, useLocation } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { BRAND } from "../lib/brand";
import { useHead } from "../lib/head";
import { useDataset, useManifest } from "../lib/data";
import { fmtDate } from "../lib/status";

// Navigation as numbered programme plates. "F1" opens the home page.
const NAV = [
  ["/", "Home"], ["/research", "Research"], ["/moneyball", "F1 Moneyball"], ["/lab", "Econometrics Lab"],
  ["/data", "Data Explorer"], ["/methodology", "Methodology"], ["/faq", "FAQ"], ["/about", "About"],
] as const;

/** Five start lights. Used as the loading indicator. */
export function StartLights({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 text-sm text-muted">
      <span aria-hidden className="flex gap-1.5">
        {Array.from({ length: 5 }, (_, i) => (
          <span key={i} className="w-3 h-3 rounded-full bg-[#5a1b1b] motion-safe:animate-[lights_1.5s_ease-in-out_infinite]" style={{ animationDelay: `${i * 0.18}s` }} />
        ))}
      </span>
      {label}…
      <style>{"@keyframes lights{0%,100%{background:#3a1414}40%,60%{background:#e5372a}}"}</style>
    </div>
  );
}

/** Status line: every value is read from the pipeline manifest. */
function StatusLine() {
  const m = useManifest();
  const q = m?.quality;
  const items: [string, string, string?][] = m ? [
    ["Data", fmtDate(m.generated_at_utc)],
    ["Datasets", String(Object.keys(m.datasets).length)],
    ["Validation", q ? (q.n_errors ? `${q.n_errors} errors` : "passed") : "not run", q && !q.n_errors ? "gain" : "loss"],
  ] : [];
  return (
    <div className="border-b border-line bg-bg">
      <div className="mx-auto max-w-6xl px-5 py-1.5 flex items-center justify-between gap-4 font-mono text-[0.68rem] uppercase tracking-[0.08em] text-muted">
        <span className="flex items-center gap-2"><span aria-hidden className="w-1.5 h-1.5 rounded-full bg-race" />Race programme · research edition</span>
        <span className="hidden sm:flex gap-5">
          {m === undefined && <span>Loading…</span>}
          {m === null && <span>Pipeline not yet run</span>}
          {items.map(([k, v, tone]) => <span key={k}>{k} <span className={tone ?? "text-fg"}>{v}</span></span>)}
        </span>
      </div>
    </div>
  );
}

const fmtPts = (v: number) => (Number.isInteger(v) ? String(v) : v.toFixed(1));

/** Standings tape: the latest season's constructors with the change from the season before. Real data only. */
function Ticker() {
  const { status, rows } = useDataset("constructor_season");
  const tape = useMemo(() => {
    if (status !== "ready" || !rows.length) return null;
    const latest = Math.max(...rows.map((r) => Number(r.season)));
    const prev = new Map(rows.filter((r) => Number(r.season) === latest - 1).map((r) => [String(r.team_id), r]));
    const cur = rows.filter((r) => Number(r.season) === latest).sort((a, b) => Number(a.position) - Number(b.position));
    return { latest, items: cur.map((r) => {
      const p = prev.get(String(r.team_id));
      return { id: String(r.team_id), name: String(r.team_name), pos: Number(r.position), pts: Number(r.points),
               d: p ? Number(r.points) - Number(p.points) : null };
    }) };
  }, [status, rows]);
  if (!tape) return null;
  const run = (dup: boolean) => (
    <ul className="flex shrink-0" {...(dup ? { "aria-hidden": true, "data-dup": "" } : {})}>
      {tape.items.map((t) => (
        <li key={t.id} className="flex items-baseline gap-2 px-5 border-r border-line whitespace-nowrap">
          <span className="text-accent-fg">P{t.pos}</span>
          <span className="text-head uppercase">{t.name}</span>
          <span className="text-fg">{fmtPts(t.pts)} pts</span>
          {t.d !== null && (
            <span className={t.d > 0 ? "gain" : t.d < 0 ? "loss" : "text-muted"}>
              <span aria-hidden>{t.d > 0 ? "▲" : t.d < 0 ? "▼" : "■"}</span>
              <span className="sr-only">{t.d > 0 ? "up" : t.d < 0 ? "down" : "unchanged"}</span> {fmtPts(Math.abs(t.d))}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
  return (
    <div className="bg-raise border-b border-line flex items-stretch font-mono text-[0.75rem]">
      <div className="shrink-0 bg-accent text-head font-semibold uppercase tracking-wider px-3 py-1.5 flex items-center">
        {tape.latest} standings <span className="hidden sm:inline">&nbsp;· Δ pts vs {tape.latest - 1}</span>
      </div>
      <div className="ticker overflow-hidden flex-1 py-1.5" tabIndex={0} aria-label={`${tape.latest} constructors' standings and points change from ${tape.latest - 1}`}>
        <div className="ticker-track">{run(false)}{run(true)}</div>
      </div>
    </div>
  );
}

export default function Layout() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  useHead();
  useEffect(() => { setOpen(false); window.scrollTo(0, 0); }, [pathname]);
  const link = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 font-mono uppercase tracking-[0.06em] text-[0.78rem] px-2.5 py-2 border-b-2 ${isActive ? "border-accent text-accent-fg" : "border-transparent text-fg hover:text-head hover:border-line"}`;
  const items = NAV.map(([to, label], i) => (
    <NavLink key={to} to={to} end={to === "/"} className={link}>
      <span aria-hidden className="key">F{i + 1}</span>{label}
    </NavLink>
  ));
  return (
    <div className="min-h-screen flex flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-2 focus:bg-bg">Skip to content</a>
      <header className="bg-panel">
        <StatusLine />
        <div className="mx-auto max-w-6xl px-5 py-4 flex items-center justify-between gap-6">
          <Link to="/" className="flex items-center gap-3">
            {/* Race-number plate: a livery motif, not a team mark. */}
            <span aria-hidden className="font-display font-bold italic text-[1.7rem] leading-none bg-race text-head px-2 py-1 -skew-x-12">F1</span>
            <span>
              <span className="block font-display font-bold italic uppercase text-[1.9rem] md:text-[2.2rem] leading-none tracking-wide text-head">{BRAND.name.replace(/^F1 /, "")}</span>
              <span className="block font-serif italic text-sm text-muted mt-1">{BRAND.tagline}</span>
            </span>
          </Link>
          <nav className="hidden lg:flex gap-0.5" aria-label="Main">{items}</nav>
          <button className="lg:hidden font-mono text-xs uppercase tracking-wider text-fg border border-line px-3 py-1.5" aria-expanded={open} aria-controls="mobile-nav" onClick={() => setOpen(!open)}>
            {open ? "Close" : "Menu"}
          </button>
        </div>
        {open && <nav id="mobile-nav" className="lg:hidden mx-auto max-w-6xl px-5 pb-4 flex flex-col" aria-label="Mobile">{items}</nav>}
        <div className="kerb" aria-hidden />
        <Ticker />
      </header>
      <main id="main" className="flex-1"><Outlet /></main>
      <footer className="mt-24 bg-panel border-t border-line">
        <div className="kerb" aria-hidden />
        <div className="mx-auto max-w-6xl px-5 py-10 grid gap-8 md:grid-cols-[1fr_2fr] text-sm">
          <div>
            <div className="font-display font-bold italic uppercase text-2xl text-head">{BRAND.name}</div>
            <p className="mt-1 font-serif italic text-muted">{BRAND.tagline}</p>
            <p className="mt-3 text-muted">{BRAND.positioning}</p>
          </div>
          <div>
            <p className="text-muted leading-relaxed">{BRAND.disclaimer}</p>
            <p className="mt-4 flex flex-wrap gap-x-5 gap-y-1 font-mono text-xs uppercase tracking-wider">
              <Link className="hover:text-accent-fg" to="/changelog">Changelog</Link>
              <Link className="hover:text-accent-fg" to="/methodology">Methodology</Link>
              <Link className="hover:text-accent-fg" to="/faq">FAQ</Link>
              <Link className="hover:text-accent-fg" to="/data">Data and downloads</Link>
            </p>
          </div>
        </div>
        <div className="chequer opacity-50" aria-hidden />
      </footer>
    </div>
  );
}
