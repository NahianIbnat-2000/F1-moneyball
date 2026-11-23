// Prints article and brand data as JSON for scripts/og_images.py.
import { ARTICLES } from "../src/lib/articles";
import { BRAND } from "../src/lib/brand";
console.log(JSON.stringify({ brand: BRAND, articles: ARTICLES.map((a) => ({ slug: a.slug, title: a.title, dek: a.dek, module: a.module })) }));
