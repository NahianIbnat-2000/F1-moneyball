// Central chart theme (paddock-terminal surface). Every chart reads its styling from here.
export const FG = "#E4E1D8";
export const MUTED = "#98A2A8";
export const LINE = "#252E36";
export const ACCENT = "#F5A524";
export const ACCENT_FG = "#F7B54A";
export const BG = "#0A0D10";
export const SERIES = "#3987e5"; // single-series colour: validated dark palette, slot 1
// Kept for older imports.
export const GOLD = ACCENT;
export const PAPER = BG;

export const AXIS = {
  gridcolor: "#1B2229", zerolinecolor: "#3A444D", linecolor: MUTED, showline: true, ticks: "outside" as const, tickcolor: MUTED,
  tickfont: { family: "JetBrains Mono, monospace", size: 11, color: MUTED },
  title: { font: { family: "Barlow, sans-serif", size: 13, color: FG } },
};

// Data-quality encoding, never colour alone:
//   filled marker = reported (audited or official); hollow marker = estimate; hatched bar = estimate
export const SYMBOL = { reported: "circle", estimate: "circle-open" } as const;
export const BAR_PATTERN_ESTIMATE = { shape: "/" as const, fgcolor: BG, size: 6 };

export const FONT = { family: "Barlow, sans-serif", color: FG, size: 12 };
export const HOVER = { bgcolor: "#12171C", bordercolor: ACCENT, font: { color: FG, family: "JetBrains Mono, monospace", size: 12 } };
