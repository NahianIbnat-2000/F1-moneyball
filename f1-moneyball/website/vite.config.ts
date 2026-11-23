import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { visualizer } from "rollup-plugin-visualizer";

// BASE_PATH is set by the deploy workflow to "/<repo-name>/" for GitHub Pages.
// ANALYZE=1 writes a bundle report to bundle-report.html.
export default defineConfig({
  base: process.env.BASE_PATH ?? "/",
  plugins: [
    react(), tailwindcss(),
    ...(process.env.ANALYZE ? [visualizer({ filename: "bundle-report.html", gzipSize: true, template: "treemap" })] : []),
  ],
  // PREVIEW builds embed fonts as data URIs (some sandboxed hosts allow no other font source).
  build: { chunkSizeWarningLimit: 1200, ...(process.env.VITE_PREVIEW ? { assetsInlineLimit: 200_000 } : {}) },
});
