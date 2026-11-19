// Central chart theme (dark pit-wall surface). Every chart reads its styling from here.
export const FG = "#E8E5DF";
export const MUTED = "#9CA5A2";
export const LINE = "#2D383F";
export const ACCENT = "#B58A52";
export const ACCENT_FG = "#D4AA6E";
export const BG = "#14191C";
export const SERIES = "#3987e5"; // single-series colour: validated dark palette, slot 1
// Kept for older imports.
export const GOLD = ACCENT;
export const PAPER = BG;

export const AXIS = {
  gridcolor: "#232C32", zerolinecolor: "#3A464D", linecolor: MUTED, showline: true, ticks: "outside" as const, tickcolor: MUTED,
  tickfont: { family: "JetBrains Mono, monospace", size: 11, color: MUTED },
  title: { font: { family: "Barlow, sans-serif", size: 13, color: FG } },
};

// Data-quality encoding, never colour alone:
//   filled marker = reported (audited or official); hollow marker = estimate; hatched bar = estimate
export const SYMBOL = { reported: "circle", estimate: "circle-open" } as const;
export const BAR_PATTERN_ESTIMATE = { shape: "/" as const, fgcolor: BG, size: 6 };

export const FONT = { family: "Barlow, sans-serif", color: FG, size: 12 };
export const HOVER = { bgcolor: "#0B0F11", bordercolor: ACCENT, font: { color: FG, family: "Barlow, sans-serif" } };
