// Central chart theme (race-programme livery, light surface). Every chart reads its styling from here.
export const FG = "#13294B";
export const MUTED = "#40536D";
export const LINE = "#C4D9E6";
export const ACCENT = "#F26B21";
export const ACCENT_FG = "#B3470F";
export const BG = "#FFFFFF";
export const SERIES = "#2a78d6"; // single-series colour: validated light palette, slot 1
// Kept for older imports.
export const GOLD = ACCENT;
export const PAPER = BG;

export const AXIS = {
  gridcolor: "#E3EDF3", zerolinecolor: "#8FA6BD", linecolor: MUTED, showline: true, ticks: "outside" as const, tickcolor: MUTED,
  tickfont: { family: "DM Mono, monospace", size: 11, color: MUTED },
  title: { font: { family: "Work Sans, sans-serif", size: 13, color: FG } },
};

// Data-quality encoding, never colour alone:
//   filled marker = reported (audited or official); hollow marker = estimate; hatched bar = estimate
export const SYMBOL = { reported: "circle", estimate: "circle-open" } as const;
export const BAR_PATTERN_ESTIMATE = { shape: "/" as const, fgcolor: BG, size: 6 };

export const FONT = { family: "Work Sans, sans-serif", color: FG, size: 12 };
export const HOVER = { bgcolor: "#FFFFFF", bordercolor: ACCENT, font: { color: FG, family: "DM Mono, monospace", size: 12 } };
