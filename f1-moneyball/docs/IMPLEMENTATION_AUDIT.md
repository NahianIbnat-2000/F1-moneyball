# F1 Moneyball: Implementation Audit and Plan

*An Independent Formula 1 Economics & Finance Research Platform.*
Audit date: 19 November 2026. Status: Phase 1 complete, Phase 2 code written and tested against fixtures, live data pull pending first GitHub Actions run.

---

## 0. Environment audit (what existed at the start)

| Item | Finding | Consequence |
|---|---|---|
| Existing repository | None found. No GitHub account linked to this session, no local folder connected. | Repository created from scratch. You push it to GitHub yourself (instructions in README). |
| Python | 3.13 available | Package targets Python >= 3.11. |
| Node | 22.x, npm 10.x | Vite 6 + React 18 + TypeScript. |
| Network to F1 APIs | `api.jolpi.ca` and `api.openf1.org` **blocked** from the build workspace. Only PyPI and npm reachable. | No real data has been collected yet. Ingestion code is tested with small hand-written fixtures in `tests/fixtures/` (clearly marked as test fixtures, never published). The first real pull runs in GitHub Actions. |
| Financial data | No machine-readable source exists for team budgets. | Manual entry workflow with validation (section 5.3). The financial table ships **empty**. |

The website therefore shows clear "not yet published" states instead of any numbers. This follows rule 9 and 11 of the project brief: no invented data in visualizations, no mock findings shown as real.

---

## 1. System architecture

```
                 ┌───────────────────── GitHub Actions (scheduled + manual) ─────────────────────┐
 Jolpica-F1 API ─┤ ingest ─► data/raw (JSON, untouched, with retrieval log)                       │
 FastF1 / OpenF1 ┤        ─► standardize (team mapping, types, dates) ─► data/interim (Parquet)   │
 Manual CSV ─────┤        ─► validate (schema + logic checks) ── fail ─► stop, nothing published   │
 (financials,    │        ─► features (efficiency, HHI, Gini, mobility) ─► data/processed          │
 regulations)    │        ─► analysis (statsmodels / linearmodels / sklearn) ─► reports/tables     │
                 │        ─► publish (JSON + CSV + manifest + dictionaries) ─► website/public/data │
                 └────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                     Vite build (static) ─► GitHub Pages
                                                   │
                         React app reads /data/manifest.json, then only the datasets it needs
```

Key decisions:

1. **Static site, precomputed data.** GitHub Pages cannot run Python. All heavy work happens in Actions; the browser only filters and plots small JSON files.
2. **One manifest as the contract.** `website/public/data/manifest.json` lists each published dataset, its row count, coverage, sources, build time and pipeline commit. The UI reads this first. If a dataset is not in the manifest, the UI says so. This makes every displayed number traceable (rule 17).
3. **DuckDB for local querying** over the Parquet files. No database server.
4. **HashRouter** in React so deep links work on GitHub Pages without server rewrites.

---

## 2. Repository structure

```
f1-moneyball/
├── README.md, LICENSE, pyproject.toml, requirements.txt, .gitignore
├── config/
│   ├── sources.yaml          # every external source: URL, licence, rate limit, access method
│   ├── seasons.yaml          # study window and regulatory periods
│   └── team_mapping.yaml     # constructorId -> stable team lineage (e.g. force_india -> racing_point -> aston_martin)
├── data/
│   ├── raw/                  # untouched API responses, never edited (git-ignored, cached in Actions)
│   ├── interim/              # typed, standardized Parquet
│   ├── processed/            # analysis-ready tables
│   ├── published/            # copy of what the website reads
│   ├── manual/               # hand-entered financials and regulations (CSV, validated)
│   └── metadata/             # data dictionaries (YAML) and retrieval logs
├── docs/                     # this audit, methodology notes, manual-entry guide
├── notebooks/                # exploration only; never the source of published numbers
├── src/f1moneyball/
│   ├── ingestion/            # jolpica.py, fastf1_source.py (Phase 2b), openf1.py (Phase 2b)
│   ├── standardization/      # team lineage mapping, type coercion
│   ├── validation/           # schema + logic checks, quality report
│   ├── feature_engineering/  # competitive balance, efficiency
│   ├── econometrics/         # FE models, event study (Phase 3/5)
│   ├── machine_learning/     # chronological CV, baselines (Phase 5)
│   ├── publishing/           # JSON/CSV export + manifest
│   ├── utils/                # http client with rate limit + cache, provenance, logging
│   └── pipeline.py           # CLI: ingest | build | validate | publish | all
├── research/                 # article drafts (Markdown) per module
├── reports/                  # figures, tables, methodology outputs
├── tests/                    # pytest, with fixtures
├── website/                  # Vite + React + TS + Tailwind
└── .github/workflows/        # validation.yml, data_pipeline.yml, deploy.yml
```

---

## 3. Data-source feasibility matrix

| Dataset | Programmatic | Free | Coverage 2010–2025 | Reliability | Fit for question | Limitations |
|---|---|---|---|---|---|---|
| **Jolpica-F1** (results, qualifying, standings, pit stops) | Yes, REST JSON, no key | Yes | Full (results since 1950; pit stops since 2011; lap times since 1996) | High; community successor to Ergast, drop-in compatible | Core of all sporting variables | 4 req/s burst, 500 req/h sustained. Must cache and pull incrementally. Constructor IDs change with rebrands. |
| **FastF1** (timing, laps, tyres, weather) | Yes, Python library | Yes | Detailed timing from 2018 only | High for 2018+ | Operational efficiency (race pace, stints, weather) | Short history; large downloads; must cache. Only use variables tied to a research question. |
| **OpenF1** (live/historical sessions, pit lane times) | Yes, REST, no key for historical | Yes (historical) | 2023 onwards | Good | Pit-stop durations for the cost-cap era only | Too short for 2010–2025 panel. Use as a robustness source, not the main one. |
| **F1DB** | Yes, versioned CSV/SQL releases on GitHub | Yes (CC BY 4.0) | Full | High | Cross-check of Jolpica, engine supplier and chassis lineage | Release-based, not an API. Good for validation of team lineage. |
| **UK Companies House** (statutory accounts of UK-registered teams) | Partly. API gives filing history; accounts are PDFs/iXBRL | Yes (free API key) | Good for UK entities (Mercedes, Red Bull Racing, McLaren, Williams, Aston Martin, Alpine UK, Haas UK) | **Audited** | Best available financial evidence | Accounts follow legal entities, not "teams"; financial year ends differ; include non-F1 activity; filed ~9 months late. Ferrari, Sauber, AlphaTauri/RB are not UK filers. Figures must be entered manually with page references. |
| **Liberty Media filings** (F1 revenue, team payments) | Yes (SEC EDGAR) | Yes | 2017 onwards | Audited (group level) | Prize money pool, commercial context | Team-level payments not disclosed. |
| **FIA regulations** | Documents only (PDF) | Yes | 2021+ financial regs | Official | Regulation database, cost-cap limits | Manual extraction; amendments are frequent. |
| **Forbes / press budget estimates** | No | Mostly | Patchy, inconsistent | Low to medium; methods not disclosed | Only as "reputable secondary estimate" with low confidence | Not comparable across outlets or years. Never mixed with audited figures without a flag. |
| **World Bank WDI** | Yes, API | Yes | Full | High | GDP, macro controls for Grand Prix module | Annual frequency is too coarse for event effects. |
| **UN Tourism / national statistics** (Singapore STB, Statistik Austria) | Partly (some APIs, many downloads) | Yes | Varies | High | Monthly arrivals, hotel occupancy for Grand Prix module | Differences in definitions across countries; monthly data needed for event studies. Singapore and Austria both publish monthly series, so these are the first case studies. |

**Bottom line on feasibility.** The sporting side is fully feasible and automatable. The financial side is the binding constraint: realistic coverage is an **unbalanced panel of perhaps 5 to 7 UK-filing teams**, with audited figures that measure legal-entity spending, not "budget". The research design must be built around that, not around a clean 10-team budget panel that does not exist.

---

## 4. Database schemas (analysis layer)

All tables keyed and validated in `src/f1moneyball/validation/schemas.py`.

**`constructor_season`** (key: `season, team_id`)
`season, team_id, team_name, constructor_id, engine_supplier*, points, position, wins, podiums, poles*, races_entered, points_share, points_per_race, regulatory_period`
(*Phase 2b)

**`driver_season`** (key: `season, driver_id`)
`season, driver_id, driver_name, team_id, points, position, wins`

**`race_result`** (key: `season, round, driver_id`)
`season, round, race_name, date, circuit_id, driver_id, team_id, grid, position, position_text, points, laps, status, classified, is_mechanical_dnf, grid_to_finish`

**`qualifying`** (key: `season, round, driver_id`)
`season, round, driver_id, team_id, position, q1_ms, q2_ms, q3_ms, best_ms, gap_to_pole_pct`

**`financial_observation`** (key: `team_id, entity_name, financial_year_end, metric`)
Long format, one row per number, so different metrics and accounting bases are never silently combined:
`team_id, season_mapped, entity_name, entity_registration, metric (revenue | operating_costs | operating_profit | staff_costs | estimated_budget | sponsorship_revenue), value, currency, financial_year_start, financial_year_end, accounting_basis (UK GAAP FRS102 | IFRS | not stated), source_class (audited | official_disclosure | secondary_estimate | derived_estimate | missing), source_name, source_url, document_page, publication_date, retrieval_date, confidence (high | medium | low), entered_by, notes`

**`regulation_event`** (key: `event_id`)
`event_id, effective_date, season, category (financial | technical | sporting | power_unit), title, description, value, unit, source_name, source_url, source_type (primary | secondary), verified_against_primary (bool)`

**`competitive_balance`** (key: `season`)
`season, n_teams, hhi, hhi_normalized, gini, cv, sd_points, top3_share, winner_share_of_wins, spearman_rank_persistence, regulatory_period`

---

## 5. Data collection plan

### 5.1 Sporting data (automated, Jolpica)
Per season 2010–2025: constructor standings (1 call), driver standings (1), results (paged, about 3 to 5 calls), qualifying (about 3 to 5). About 200 calls for the full window, well inside 500/hour with a 0.3 s spacing. Raw responses saved as-is with a retrieval log (URL, timestamp, status, SHA-256). Completed past seasons are never re-downloaded (cache check). Only the current season refreshes on schedule.

### 5.2 Operational data (FastF1, Phase 2b)
2018+ only: stint lengths, pit-lane time, race-pace delta to fastest team. Pit stops 2011+ come from Jolpica, which is enough for the longer panel.

### 5.3 Financial data (manual, validated)
1. Look up the UK entity on Companies House (see `docs/MANUAL_FINANCIAL_ENTRY.md`).
2. Enter one row per figure in `data/manual/financial_observations.csv`, with page number.
3. `python -m f1moneyball.pipeline validate` checks: allowed enums, ISO dates, currency codes, year-end after year-start, value within a documented plausible range, a URL for every non-missing row, no duplicate keys.
4. A pull request runs the same checks in CI. Nothing is published on failure.
5. Currency conversion, if done, uses period-average rates from an official source (Bank of England series), stored as a separate derived column with the rate and date. Original values are never overwritten.

### 5.4 Regulation data (manual, seeded)
Seeded with the cost-cap path ($145M 2021, $140M 2022, $135M base 2023–2025, $215M 2026 under a wider cost definition) and the 2022 technical reset. Seed rows are sourced to secondary reporting and flagged `verified_against_primary = false` until checked against the FIA Financial Regulations PDFs.

---

## 6. Initial research methodology (and where the brief needs tightening)

**6.1 Money and performance.** Baseline: `log(points + 1)_it = β log(Resources_it) + α_i + γ_t + ε_it` with team-clustered SEs.
*Critical issue:* with team and season fixed effects and about 6 teams × 12 years, β is identified only from within-team changes in spending over time. Those changes are small and slow, so β will be imprecise. Also, reverse causality is real: success raises prize money and sponsorship, which raises spending next year. Plan: report pooled, team FE and TWFE side by side; use lagged resources (t−1) as the main regressor; present results as associations. No causal language.

**6.2 Financial efficiency.** `PointsShare_it / ResourceShare_it`.
*Critical issue:* "resource share" needs all teams' resources in the same season. With an unbalanced panel, the denominator is wrong. Fix: compute shares only within the set of teams with comparable audited figures that year, and show the coverage next to every ranking. Also report a rank-based version (points rank vs resource rank), which is less sensitive to accounting differences.

**6.3 Competitive balance.** HHI, normalized HHI, Gini, CV, top-3 share, Spearman rank persistence (t vs t−1). Fully computable from Jolpica. This is the most robust module and should ship first.

**6.4 Cost cap.** Pre (2014–2020) vs post (2021–2025) with an interrupted time series on balance indices.
*Critical issue:* there is no untreated control group (all teams were capped), and 2021 cap and 2022 technical reset are one year apart, so the two effects cannot be separated with season-level data. A defensible design is **dose-response DiD**: teams that had to cut more (big spenders, identified from audited pre-2021 accounts) vs teams already below the cap. Treatment intensity = pre-period spending above $145M. Even this is confounded by the 2022 reset if big spenders adapted differently. We present it as suggestive evidence with placebo years.

**6.5 Operational efficiency.** Regress points share on reliability (mechanical DNF rate), grid-to-finish gain and median pit-lane time, controlling for qualifying pace. Qualifying pace absorbs most of "car speed", so the residual is a reasonable operational signal.

**6.6 Machine learning.** Target: next-season points share. Features available before the season (lagged points, lagged rank, team continuity, engine supplier, regulatory reset dummy). Expanding-window CV by season. Baselines: last season's share, and a linear model. With about 160 team-seasons, expect Ridge to match or beat Random Forest. Report that honestly.

**6.7 Grand Prix economy.** Monthly tourist arrivals/hotel occupancy, event study around race month, synthetic control using comparable non-hosting destinations. Clear split of gross vs additional vs displaced spending. If pre-period fit is poor, publish descriptive analysis only.

---

## 7. Frontend page structure

| Route | Content | Data needed |
|---|---|---|
| `/` Home | Hero "Does Money Buy Speed?", featured series "The Economics of Competitive Advantage", modules, pipeline status | manifest |
| `/research` | Article library with status (draft / in progress / published) | `research/*.md` index |
| `/moneyball` | Money vs performance, efficiency ranking, resources over time, performance matrix, trajectories | constructor_season, financial_observation |
| `/cost-cap` | Balance time series, regulation timeline, pre/post, identification notes | competitive_balance, regulation_event |
| `/grand-prix-economy` | Case studies (Singapore, Austria), method, status | tourism series (Phase 6) |
| `/data` | Dataset picker, filters, sortable table, CSV download, dictionary, provenance | manifest + any dataset |
| `/methodology` | Sources, cleaning, classifications, models, limitations, reproduction | static + dictionaries |
| `/about` | Mission, disclaimer, author | static |

---

## 8. Deployment strategy

1. Push to GitHub. Enable Pages with "GitHub Actions" as source.
2. `data_pipeline.yml` (weekly + manual): ingest → build → validate → publish → commit `website/public/data` **only if validation passes**.
3. `validation.yml` (PRs): pytest, schema checks, frontend type-check and build, secret scan (gitleaks).
4. `deploy.yml` (push to main): build site with correct base path, deploy to Pages.

---

## 9. Risks and limitations

| Risk | Severity | Mitigation |
|---|---|---|
| Financial panel is small and unbalanced | High | Design around it; show coverage on every chart; prefer within-team and rank-based measures. |
| Legal-entity accounts ≠ team budget (engine, non-F1 work, year-end mismatch) | High | Long-format table with accounting basis; never mix bases; map financial year to season explicitly. |
| Cost cap and 2022 technical reset nearly simultaneous | High | Dose-response design, placebo tests, explicit "cannot separate" statements. |
| Reverse causality (points → money) | High | Lagged regressors; no causal claims. |
| Team rebrands break panels | Medium | Lineage mapping in `team_mapping.yaml`, tested. |
| Jolpica rate limits / downtime | Medium | Cache, incremental pulls, retries with backoff, pipeline fails without publishing. |
| Points system changes (sprints from 2021, fastest-lap point 2019–2024) | Medium | Use shares and ranks, not raw points, for cross-era comparison. |
| Plotly bundle size | Low | Use the `plotly.js-basic-dist-min` build and lazy-load chart pages. |

---

## 10. Prioritized roadmap

| # | Milestone | Status |
|---|---|---|
| 1 | Repo, design system, website shell, docs | **Done** |
| 2 | Jolpica ingestion, team lineage, validation, balance metrics, publish + manifest | **Code done, tested on fixtures**; needs first Actions run |
| 3 | Competitive balance charts live (Cost Cap module, descriptive) | Next: runs as soon as data lands |
| 4 | Companies House manual entry for UK teams 2012–2024 | Needs your time (est. 6 to 10 hours) |
| 5 | Efficiency framework + FE regressions + first article | After 4 |
| 6 | FastF1 operational features (2018+) | |
| 7 | ML module with chronological CV | |
| 8 | Grand Prix Economy (Singapore, Austria) | |
| 9 | Accessibility, performance, polish | |
