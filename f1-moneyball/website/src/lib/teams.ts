// Colour follows the team lineage, never its rank, and never changes with filters.
// Eight validated slots; remaining lineages are drawn in neutral grey as "Other teams".
export const TEAM_COLOR: Record<string, string> = {
  red_bull: "var(--color-series-1)", mclaren: "var(--color-series-2)", mercedes: "var(--color-series-3)",
  ferrari: "var(--color-series-8)", silverstone: "var(--color-series-6)", enstone: "var(--color-series-5)",
  williams: "var(--color-series-7)", faenza: "var(--color-series-4)",
};
// Plotly needs resolved hex values, not CSS variables.
const HEX: Record<string, string> = {
  "var(--color-series-1)": "#3987e5", "var(--color-series-2)": "#d95926", "var(--color-series-3)": "#199e70",
  "var(--color-series-4)": "#c98500", "var(--color-series-5)": "#d55181", "var(--color-series-6)": "#0ca30c",
  "var(--color-series-7)": "#9085e9", "var(--color-series-8)": "#e66767",
};
export const OTHER = "#6B7579";
export const teamHex = (id: string) => HEX[TEAM_COLOR[id]] ?? OTHER;
