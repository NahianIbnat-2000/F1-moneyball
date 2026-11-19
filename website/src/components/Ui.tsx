import type { ReactNode } from "react";

export function PageHeader({ eyebrow, title, lede, children }: { eyebrow: string; title: string; lede?: string; children?: ReactNode }) {
  return (
    <section className="mx-auto max-w-6xl px-5 pt-12 pb-8">
      <div className="eyebrow">{eyebrow}</div>
      <h1 className="font-serif italic uppercase text-5xl md:text-[4rem] leading-[0.95] font-bold text-head mt-3 max-w-4xl">{title}</h1>
      {lede && <p className="mt-5 text-xl text-fg/85 max-w-3xl leading-relaxed">{lede}</p>}
      {children}
      <div className="mt-8 border-b border-line" />
    </section>
  );
}

export function Section({ title, eyebrow, children, id }: { title?: string; eyebrow?: string; children: ReactNode; id?: string }) {
  return (
    <section id={id} className="mx-auto max-w-6xl px-5 py-10">
      {(title || eyebrow) && (
        <div className="border-t border-line pt-4 mb-6">
          {eyebrow && <div className="eyebrow">{eyebrow}</div>}
          {title && <h2 className="font-serif uppercase text-3xl md:text-[2.3rem] font-bold text-head leading-tight mt-1">{title}</h2>}
        </div>
      )}
      {children}
    </section>
  );
}

/** A marginal note: a ruled aside, not a coloured box. */
export function Callout({ title, children, tone = "note" }: { title: string; children: ReactNode; tone?: "note" | "caution" }) {
  return (
    <aside className={`border-l-2 ${tone === "caution" ? "border-accent" : "border-fg/70"} pl-4 py-1`}>
      <div className="font-serif uppercase tracking-wide font-semibold text-head">{title}</div>
      <div className="mt-1 text-sm text-fg/85 leading-relaxed">{children}</div>
    </aside>
  );
}
