// Thin wrapper around the small Plotly build, with shared editorial styling.
import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-basic-dist-min";
import type { Layout, Data, Config } from "plotly.js";

const PlotlyComponent = createPlotlyComponent(Plotly);

import { AXIS, FONT, HOVER } from "../lib/chartTheme";

export default function PlotImpl({ data, layout, height = 380, ariaLabel }: { data: Data[]; layout?: Partial<Layout>; height?: number; ariaLabel: string }) {
  // Toolbar hidden: its controls are not keyboard or crawler friendly. Downloads are buttons in ChartFrame.
  const config: Partial<Config> = { displaylogo: false, responsive: true, displayModeBar: false };
  return (
    <div role="img" aria-label={ariaLabel}>
      <PlotlyComponent
        data={data}
        layout={{
          height, autosize: true, margin: { l: 64, r: 24, t: 16, b: 52 },
          paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
          font: FONT, hoverlabel: HOVER,
          showlegend: false, ...layout,
          xaxis: { ...AXIS, ...layout?.xaxis }, yaxis: { ...AXIS, ...layout?.yaxis },
        }}
        config={config}
        style={{ width: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
