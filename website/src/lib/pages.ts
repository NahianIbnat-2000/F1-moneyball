// Page metadata: one source for the in-app <title> and the build-time static <head>.
import { ARTICLES } from "./articles";
import { BRAND } from "./brand";

export interface PageMeta { path: string; title: string; description: string; type: "website" | "article"; image: string }

const site = (title: string) => `${title} · ${BRAND.name}`;

export const PAGES: PageMeta[] = [
  { path: "/", title: `${BRAND.name} · ${BRAND.tagline}`, description: `${BRAND.headline} ${BRAND.positioning}`, type: "website", image: "og/default.png" },
  { path: "/research", title: site("Research"), description: `${BRAND.series} Research designs, data and results on the economics of Formula 1.`, type: "website", image: "og/default.png" },
  { path: "/moneyball", title: site("F1 Moneyball laboratory"), description: "How efficiently do Formula 1 teams convert financial resources into sporting performance? Charts, efficiency measures and models.", type: "website", image: "og/does-money-buy-speed.png" },
  { path: "/cost-cap", title: site("The Cost Cap Paradox"), description: "Did the introduction of the Formula 1 cost cap change competitive balance? Research in progress.", type: "website", image: "og/cost-cap-paradox.png" },
  { path: "/grand-prix-economy", title: site("The Grand Prix Economy"), description: "Does hosting a Formula 1 Grand Prix generate net additional economic benefits for the host economy? Research in progress.", type: "website", image: "og/grand-prix-economy.png" },
  { path: "/data", title: site("Data Explorer"), description: "Every F1 Moneyball dataset with its status, data dictionary, missing values, sources and CSV downloads.", type: "website", image: "og/default.png" },
  { path: "/methodology", title: site("Methodology"), description: "Sources, cleaning, definitions, financial-data classifications, limitations and how to reproduce F1 Moneyball.", type: "website", image: "og/default.png" },
  { path: "/changelog", title: site("Changelog"), description: "New data, corrected data, methodological changes, revised analysis, publications and website changes.", type: "website", image: "og/default.png" },
  { path: "/about", title: site("About"), description: BRAND.disclaimer, type: "website", image: "og/default.png" },
  ...ARTICLES.map((a): PageMeta => ({ path: `/research/${a.slug}`, title: site(a.title), description: a.dek, type: "article", image: `og/${a.slug}.png` })),
];

export const pageMeta = (path: string) => PAGES.find((p) => p.path === path.replace(/\/$/, "") || (p.path === "/" && path === ""));
