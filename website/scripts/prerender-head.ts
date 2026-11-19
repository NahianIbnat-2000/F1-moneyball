/**
 * Build step: write one static HTML file per route with its own <head>
 * (title, description, canonical, Open Graph, Twitter card, JSON-LD), plus
 * 404.html (SPA fallback for GitHub Pages), robots.txt and, if SITE_URL is set, sitemap.xml.
 * The page body is still rendered by React in the browser.
 *
 * SITE_URL (e.g. https://user.github.io/f1-moneyball/) is set by the deploy workflow.
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { ARTICLES } from "../src/lib/articles";
import { BRAND } from "../src/lib/brand";
import { PAGES } from "../src/lib/pages";

const dist = join(import.meta.dirname, "..", "dist");
const site = (process.env.SITE_URL ?? "").replace(/\/?$/, "/");
const hasSite = site !== "/";
const template = readFileSync(join(dist, "index.html"), "utf8");
const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");

function head(p: (typeof PAGES)[number]) {
  // GitHub Pages serves /path/index.html at /path/, so canonical URLs end in a slash.
  const rel = p.path === "/" ? "" : `${p.path.slice(1)}/`;
  const url = hasSite ? site + rel : "";
  const img = hasSite ? site + p.image : "";
  const article = ARTICLES.find((a) => `/research/${a.slug}` === p.path);
  const ld = article
    ? { "@context": "https://schema.org", "@type": "Article", headline: article.title, description: article.dek,
        author: { "@type": "Person", name: article.author }, dateModified: article.draftRevised,
        ...(article.publishedOn ? { datePublished: article.publishedOn } : {}),
        isPartOf: { "@type": "CreativeWorkSeries", name: BRAND.series.replace(/\.$/, "") },
        ...(url ? { url, mainEntityOfPage: url } : {}), ...(img ? { image: img } : {}),
        citation: article.references.map((r) => `${r.authors} (${r.year}). ${r.title}. ${r.venue}.`) }
    : p.path === "/" ? { "@context": "https://schema.org", "@type": "WebSite", name: BRAND.name, description: BRAND.positioning, ...(url ? { url } : {}) } : null;
  return [
    `<title>${esc(p.title)}</title>`,
    `<meta name="description" content="${esc(p.description)}" />`,
    url && `<link rel="canonical" href="${url}" />`,
    `<meta property="og:site_name" content="${BRAND.name}" />`,
    `<meta property="og:type" content="${p.type}" />`,
    `<meta property="og:title" content="${esc(p.title)}" />`,
    `<meta property="og:description" content="${esc(p.description)}" />`,
    url && `<meta property="og:url" content="${url}" />`,
    img && `<meta property="og:image" content="${img}" />`,
    img && `<meta property="og:image:width" content="1200" /><meta property="og:image:height" content="630" />`,
    `<meta name="twitter:card" content="summary_large_image" />`,
    `<meta name="twitter:title" content="${esc(p.title)}" />`,
    `<meta name="twitter:description" content="${esc(p.description)}" />`,
    img && `<meta name="twitter:image" content="${img}" />`,
    ld && `<script type="application/ld+json">${JSON.stringify(ld)}</script>`,
  ].filter(Boolean).join("\n    ");
}

// Remove the template's own title/description/og tags, then insert the page's.
const stripped = template
  .replace(/<title>[\s\S]*?<\/title>\s*/, "")
  .replace(/<meta (name="description"|property="og:[^"]+")[^>]*>\s*/g, "");

for (const p of PAGES) {
  const html = stripped.replace("</head>", `    ${head(p)}\n  </head>`);
  const out = p.path === "/" ? join(dist, "index.html") : join(dist, p.path.slice(1), "index.html");
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, html);
}
writeFileSync(join(dist, "404.html"), stripped.replace("</head>", `    <title>Page not found · ${BRAND.name}</title>\n    <meta name="robots" content="noindex" />\n  </head>`));
writeFileSync(join(dist, "robots.txt"), `User-agent: *\nAllow: /\n${hasSite ? `Sitemap: ${site}sitemap.xml\n` : ""}`);
if (hasSite) {
  writeFileSync(join(dist, "sitemap.xml"), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${PAGES.map((p) => `  <url><loc>${site}${p.path === "/" ? "" : `${p.path.slice(1)}/`}</loc></url>`).join("\n")}\n</urlset>\n`);
}
console.log(`prerender-head: ${PAGES.length} pages${hasSite ? ` for ${site}` : " (SITE_URL not set: no canonical, og:url, og:image or sitemap)"}`);
