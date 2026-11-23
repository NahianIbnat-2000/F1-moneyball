import { lazy, Suspense, useEffect, useRef, useState } from "react";
import type { Layout, Data } from "plotly.js";
import { StartLights } from "./Layout";

// Plotly (about 1 MB) is downloaded only when a chart comes near the screen.
const PlotImpl = lazy(() => import("./PlotImpl"));

export default function Plot(props: { data: Data[]; layout?: Partial<Layout>; height?: number; ariaLabel: string }) {
  const h = props.height ?? 380;
  const ref = useRef<HTMLDivElement>(null);
  const [near, setNear] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || near) return;
    if (!("IntersectionObserver" in window)) { setNear(true); return; }
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { setNear(true); io.disconnect(); } }, { rootMargin: "300px" });
    io.observe(el);
    return () => io.disconnect();
  }, [near]);
  const placeholder = <div style={{ height: h }} className="flex items-center justify-center bg-raise/40"><StartLights label="Loading chart" /></div>;
  return (
    <div ref={ref} style={{ minHeight: h }}>
      {near ? <Suspense fallback={placeholder}><PlotImpl {...props} /></Suspense> : placeholder}
    </div>
  );
}
