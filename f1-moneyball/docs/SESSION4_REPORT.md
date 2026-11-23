# Session 4 report: racing theme, Cost Cap Paradox and Grand Prix Economy

Date: 19 November 2026

## Theme
Changed at the owner's request from an editorial print look to a racing "pit wall" theme. This
departs from the original brief's advice to avoid fan-site styling; to keep it credible:
- the approved navy and gold are used as livery colours on a carbon-dark surface; no F1 logos, team liveries or photographs;
- motifs are generic motorsport: chequered strip, kerb stripe in livery colours, race-number plate, racing line through a chicane, start lights as the loading indicator, timing-tower status panel;
- type: Barlow Condensed (display), Barlow (reading), JetBrains Mono (figures), all self-hosted;
- colour tokens renamed by role (`bg`, `fg`, `head`, `muted`, `accent`, `line`, `raise`), so the theme can change again without misleading class names;
- all text contrast measured: body 14:1, muted 7:1, gold 5.7:1 (AA);
- chart series use the validated dark-surface palette (all checks pass on the new surface).

## Cost Cap Paradox (pipeline: `econometrics/cost_cap.py`)
- Interrupted time series on 5 balance indicators: level and slope change at 2021, Newey-West errors. Spec B adds a 2022 technical-reset dummy and is labelled as resting on the 2021 season alone.
- Placebo break years within 2010–2020; the share of placebos at least as large as the 2021 change is reported.
- Dose-response: points share on exposure × post with team and season effects, exposure = standardised log mean 2018–2020 resources (one measure, one currency); event study by season, reference 2020. Requires 4 teams with pre-cap figures. Labelled suggestive.
- New datasets: `cost_cap_models`, `cost_cap_event_study`.

## Grand Prix Economy (pipeline: `econometrics/gp_economy.py`)
- Manual monthly series and race dates with validation (`data/manual/gp_tourism_monthly.csv`, `gp_race_events.csv`; guide in `docs/GP_DATA_ENTRY.md`).
- Event study per host: months −2 to +2 around races against seasonal pattern and trend, HAC errors.
- Synthetic control for race entry: simplex weights, placebo-in-space inference (RMSPE ratio rank), pre-fit rule (RMSPE above 0.10 flagged; gap not read as an effect).
- New datasets: `gp_race_events`, `gp_event_study`, `gp_scm_path`, `gp_scm_inference`.

## Pages
Cost Cap: four sectors (treatment, balance over time, ITS vs placebos CC-3, dose-response event study CC-4). Grand Prix: gross-to-net layers (6), data status, event study GP-1, synthetic control GP-2, placebo inference GP-3. Both stay labelled "Research in progress"; every chart shows the dataset status until real data exists.

## Verification
- pytest 55 passed (46 before). New tests plant known effects in synthetic data and check that each method recovers them: ITS level drop, placebo share, dose-response coefficient with flat pre-trends, race-month bump, synthetic-control weights and host rank, and refusal on short samples.
- Render test of all new charts on synthetic data in a temporary copy (deleted).
- Build under the `/f1-moneyball/` subpath: 28 pages crawled, 0 broken links, 0 console errors, 0 failed requests, no overflow at 1280/820/390 px; axe 0 violations on 9 pages.
- Lighthouse (mobile profile, uncompressed local server): Home 84, Grand Prix 92, Cost Cap 72–79 (Plotly parse time), accessibility/best practices/SEO 100 on all three after enlarging chart link targets.

## Still not possible from the build workspace
No real data: sporting data needs the Data pipeline workflow; financial and tourism data need manual entry from official documents.
