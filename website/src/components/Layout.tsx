import { NavLink, Outlet, Link, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { BRAND } from "../lib/brand";
import { useHead } from "../lib/head";

const NAV = [
  ["/", "Home"], ["/research", "Research"], ["/moneyball", "F1 Moneyball"],
  ["/data", "Data Explorer"], ["/methodology", "Methodology"], ["/about", "About"],
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
      <style>{"@keyframes lights{0%,100%{background:#3a1414}40%,60%{background:#e5484d}}"}</style>
    </div>
  );
}

export default function Layout() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  useHead();
  useEffect(() => { setOpen(false); window.scrollTo(0, 0); }, [pathname]);
  const link = ({ isActive }: { isActive: boolean }) =>
    `font-serif uppercase tracking-wider text-[0.95rem] px-3 py-2 -skew-x-12 ${isActive ? "bg-accent text-bg" : "text-fg hover:bg-raise"}`;
  return (
    <div className="min-h-screen flex flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-2 focus:bg-bg">Skip to content</a>
      <header className="bg-navy">
        <div className="chequer opacity-80" aria-hidden />
        <div className="mx-auto max-w-6xl px-5 py-4 flex items-center justify-between gap-6">
          <Link to="/" className="flex items-center gap-3 group">
            {/* Race-number plate: a livery motif, not a team mark. */}
            <span aria-hidden className="font-serif font-bold italic text-2xl leading-none bg-accent text-bg px-2 py-1 -skew-x-12">F1</span>
            <span>
              <span className="block font-serif font-bold italic uppercase text-2xl md:text-3xl leading-none tracking-wide text-head">{BRAND.name.replace(/^F1 /, "")}</span>
              <span className="block text-xs text-accent-fg tracking-wide mt-1">{BRAND.tagline}</span>
            </span>
          </Link>
          <nav className="hidden lg:flex gap-1" aria-label="Main">
            {NAV.map(([to, label]) => <NavLink key={to} to={to} end={to === "/"} className={link}><span className="inline-block skew-x-12">{label}</span></NavLink>)}
          </nav>
          <button className="lg:hidden font-serif uppercase tracking-wider text-fg border border-line px-3 py-1" aria-expanded={open} aria-controls="mobile-nav" onClick={() => setOpen(!open)}>
            {open ? "Close" : "Menu"}
          </button>
        </div>
        {open && (
          <nav id="mobile-nav" className="lg:hidden mx-auto max-w-6xl px-5 pb-4 flex flex-col gap-1" aria-label="Mobile">
            {NAV.map(([to, label]) => <NavLink key={to} to={to} end={to === "/"} className={link}><span className="inline-block skew-x-12">{label}</span></NavLink>)}
          </nav>
        )}
        <div className="kerb" aria-hidden />
      </header>
      <main id="main" className="flex-1"><Outlet /></main>
      <footer className="mt-24 bg-navy">
        <div className="kerb" aria-hidden />
        <div className="mx-auto max-w-6xl px-5 py-8 grid gap-6 md:grid-cols-[1fr_2fr] text-sm">
          <div>
            <div className="font-serif font-bold italic uppercase text-2xl text-head">{BRAND.name}</div>
            <p className="mt-1 text-muted">{BRAND.positioning}</p>
          </div>
          <div>
            <p className="text-muted leading-relaxed">{BRAND.disclaimer}</p>
            <p className="mt-3 flex flex-wrap gap-x-5 gap-y-1">
              <Link className="underline decoration-accent underline-offset-2" to="/changelog">Changelog</Link>
              <Link className="underline decoration-accent underline-offset-2" to="/methodology">Methodology</Link>
              <Link className="underline decoration-accent underline-offset-2" to="/data">Data and downloads</Link>
            </p>
          </div>
        </div>
        <div className="chequer opacity-60" aria-hidden />
      </footer>
    </div>
  );
}
