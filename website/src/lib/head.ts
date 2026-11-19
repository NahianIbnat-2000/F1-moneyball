import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { pageMeta } from "./pages";

/** Keeps <title> and the meta description in step with client-side navigation. */
export function useHead() {
  const { pathname } = useLocation();
  useEffect(() => {
    const base = import.meta.env.BASE_URL.replace(/\/$/, "");
    const m = pageMeta(pathname.startsWith(base) ? pathname.slice(base.length) || "/" : pathname);
    if (!m) return;
    document.title = m.title;
    document.querySelector('meta[name="description"]')?.setAttribute("content", m.description);
  }, [pathname]);
}
