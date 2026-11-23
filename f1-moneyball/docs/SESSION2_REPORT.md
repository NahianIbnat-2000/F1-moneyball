# Session 2 report: theme and flagship analysis

Date: 19 November 2026

## Data situation (read first)
Real data could not be collected in this session. From the build workspace, the Jolpica-F1 API and GitHub (F1DB releases) are blocked by the network policy, and the owner's computer was not connected. npm hosts F1 data only through unvetted third-party repackagers, which were not used. **No result on the site is computed from real sporting or financial data yet.** Everything below runs automatically once (1) the Data pipeline workflow runs and (2) financial figures are entered.

## Theme
Replaced the dashboard-like look with an editorial broadsheet language, keeping the approved palette and fonts:
- Masthead nameplate with tagline; thick and thin rules instead of a dark navbar and hero.
- Serif reading text, drop cap on the lead, italic section kickers. Removed uppercase tracked monospace labels, pill badges, card grids, dashed placeholder boxes and the decorative line motif.
- Status shown as text with a shape mark (● published, ○ not published), never colour alone.
- Tables use horizontal rules only. Charts are numbered figures ("Figure MB-1").
- Central chart theme: `website/src/lib/chartTheme.ts`.

## Pipeline (new)
- `econometrics/efficiency.py`: financial panel (one figure per team, season, measure; multi-entity rows excluded with reason) and efficiency indicators computed within comparison groups of season x measure x currency with at least 4 teams. Measures: efficiency ratio, points per million, rank gap. Excluded rows are kept with `exclusion_reason`.
- `econometrics/models.py`: points share on lagged log resources: pooled OLS, team FE, two-way FE, standard errors clustered by team, 95% CI, R², economic size (pp change per +10% resources), sample-size rules and few-cluster warnings. Models are refused below 20 observations, 4 teams or 3 seasons.
- New datasets `efficiency` and `model_results` in the registry, dictionary, publishing and status rules (insufficient coverage when no group or model qualifies).
- Tests: 36 → 43, including recovery of a known positive coefficient on a synthetic panel and refusal on small samples.

## Flagship page (`/moneyball`)
- A. Resources vs points share / position (MB-1, MB-2), trajectories (MB-3), qualifying pace vs race-day gains (MB-4), reliability vs points (MB-5).
- B. Efficiency ratio, points per million and rank gap as three separate measures (MB-6 to MB-8), efficiency over time (MB-9). Hollow markers and hatched bars mark estimates.
- C. Constructor comparison, up to four teams, averaged over the seasons all chosen teams raced; teams without comparable financial figures show the reason.
- D. Model table (MB-11) labelled as estimates, not causal effects.
- E. Methodological safeguards.
- Every chart: figure ID, measure and currency in the axis title, coverage, version, CSV download, show-data-table toggle, text reading generated from the data, methodology link.

## Verification
- pytest 43 passed; ruff clean; tsc clean; build passes.
- Crawl: 20 routes, 0 broken links, 0 console errors. 20 routes x 3 widths: no horizontal overflow.
- Render test of every new chart against SYNTHETIC data in a scratch copy (red demo banner), then deleted. Not in the repository.

## Bundle
| File | Session 1 | Session 2 |
|---|---|---|
| index.js | 261.0 kB (84.3 gzip) | 277.3 kB (89.2 gzip) |
| plotly.js | 1,099.5 kB (377.9 gzip) | unchanged; lazy loading is Phase 3 |

## Not done
- Efficiency frontier (optional in the brief): left out until real data shows whether a frontier is meaningful with so few teams.
- Currency conversion and inflation adjustment: needs an official FX and deflator series; until then figures are nominal and compared only within one currency.
