import { lazy, Suspense } from "react";
import { BrowserRouter, MemoryRouter, Route, Routes, Link } from "react-router-dom";
import Layout, { StartLights } from "./components/Layout";
import Home from "./pages/Home";
const Research = lazy(() => import("./pages/Research"));
const Moneyball = lazy(() => import("./pages/Moneyball"));
const CostCap = lazy(() => import("./pages/CostCap"));
const GrandPrix = lazy(() => import("./pages/GrandPrix"));
const DataExplorer = lazy(() => import("./pages/DataExplorer"));
const Methodology = lazy(() => import("./pages/Methodology"));
const About = lazy(() => import("./pages/About"));
const ArticlePage = lazy(() => import("./pages/Article"));
const Changelog = lazy(() => import("./pages/Changelog"));
import { PageHeader } from "./components/Ui";
import { useManifest } from "./lib/data";

function DemoBanner() {
  const m = useManifest();
  if (!m?.is_synthetic_demo) return null;
  return <div className="bg-red-800 text-white text-center text-sm py-2">SYNTHETIC DEMO DATA. NOT REAL RESULTS.</div>;
}

// Path-based routes. GitHub Pages serves a prerendered HTML file per route (scripts/prerender-head.ts)
// and 404.html as the fallback for anything else.
// PREVIEW=1 builds a single-page preview for sandboxed hosts: in-memory routing, relative paths.
const Router = import.meta.env.VITE_PREVIEW
  ? ({ children }: { children: React.ReactNode }) => <MemoryRouter>{children}</MemoryRouter>
  : ({ children }: { children: React.ReactNode }) => <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "")}>{children}</BrowserRouter>;

export default function App() {
  return (
    <Router>
      <DemoBanner />
      <Suspense fallback={<div className="mx-auto max-w-6xl px-5 py-16"><StartLights /></div>}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="research" element={<Research />} />
          <Route path="research/:slug" element={<ArticlePage />} />
          <Route path="moneyball" element={<Moneyball />} />
          <Route path="cost-cap" element={<CostCap />} />
          <Route path="grand-prix-economy" element={<GrandPrix />} />
          <Route path="data" element={<DataExplorer />} />
          <Route path="methodology" element={<Methodology />} />
          <Route path="about" element={<About />} />
          <Route path="changelog" element={<Changelog />} />
          <Route path="*" element={<PageHeader eyebrow="404" title="Page not found"><Link className="underline mt-4 inline-block" to="/">Back to home</Link></PageHeader>} />
        </Route>
      </Routes>
      </Suspense>
    </Router>
  );
}
