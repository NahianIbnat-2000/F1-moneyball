// Colour follows the team lineage, never its rank, and never changes with filters.
// Eight validated slots; remaining lineages are drawn in neutral grey as "Other teams".
export const TEAM_COLOR: Record<string, string> = {
  red_bull: "var(--color-series-1)", mclaren: "var(--color-series-2)", mercedes: "var(--color-series-3)",
  ferrari: "var(--color-series-8)", silverstone: "var(--color-series-6)", enstone: "var(--color-series-5)",
  williams: "var(--color-series-7)", faenza: "var(--color-series-4)",
};
// Plotly needs resolved hex values, not CSS variables.
const HEX: Record<string, string> = {
  "var(--color-series-1)": "#2a78d6", "var(--color-series-2)": "#eb6834", "var(--color-series-3)": "#1baf7a",
  "var(--color-series-4)": "#eda100", "var(--color-series-5)": "#e87ba4", "var(--color-series-6)": "#008300",
  "var(--color-series-7)": "#6250d6", "var(--color-series-8)": "#e34948",
};
export const OTHER = "#8A99A8";
export const teamHex = (id: string) => HEX[TEAM_COLOR[id]] ?? OTHER;
