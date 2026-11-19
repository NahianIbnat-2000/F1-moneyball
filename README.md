# F1 Moneyball

**The Economics Behind the Speed.**
*An Independent Formula 1 Economics & Finance Research Platform.*
Featured research series: **The Economics of Competitive Advantage.**

> Does Money Buy Speed?

F1 Moneyball studies how financial resources, regulation, operational efficiency and commercial strategy shape competitive performance in Formula 1. It combines a reproducible Python data pipeline, econometrics, machine learning and an editorial research website.

## Status (milestone log)

| Milestone | Status |
|---|---|
| Implementation audit ([docs/IMPLEMENTATION_AUDIT.md](docs/IMPLEMENTATION_AUDIT.md)) | Done |
| Phase 1: repository, design system, website shell, CI/CD | Done |
| Phase 2: Jolpica-F1 ingestion, team lineage, validation, balance metrics, publishing | Code done and tested on fixtures. **First real data pull runs on the first `Data pipeline` workflow run.** |
| Financial database (Companies House, manual entry) | Schema and validator done. **Table is empty**: no figures have been entered yet. |
| Session 1 of the research-grade brief: dataset status system, article template, homepage, Data Explorer, provenance ([docs/SESSION1_AUDIT_AND_PLAN.md](docs/SESSION1_AUDIT_AND_PLAN.md)) | Done |
| Session 4: racing theme; Cost Cap (ITS, placebos, dose-response event study) and Grand Prix Economy (event study, synthetic control) methods and pages ([docs/SESSION4_REPORT.md](docs/SESSION4_REPORT.md)) | Code done and tested; **needs data** |
| Session 3: lazy loading (home JS 1,344 kB → 200 kB), path URLs with per-page metadata, citations, changelog, axe and Lighthouse checks ([docs/SESSION3_REPORT.md](docs/SESSION3_REPORT.md)) | Done |
| Session 2: editorial theme, efficiency indicators, FE models, flagship laboratory and comparison tool ([docs/SESSION2_REPORT.md](docs/SESSION2_REPORT.md)) | Code done and tested; **results appear after the first pipeline run and financial entry** |

**Published real data today:** the regulation event table (8 rows, cost-cap levels sourced to secondary reporting, flagged until checked against FIA documents). Nothing else on the site shows numbers until the pipeline has produced them.

## Quick start

```bash
pip install -e ".[dev]"
pytest                                       # 55 tests
python -m f1moneyball.pipeline all           # ingest 2010-2025, build, validate, publish
cd website && npm ci && npm run dev          # http://localhost:5173
# website/scripts/og_images.py regenerates social preview images; ANALYZE=1 npm run build writes a bundle report
```

Pipeline commands: `ingest`, `build`, `validate`, `publish`, `all` (`--start`, `--end`, `--force`).
A full first ingest makes about 200 requests to Jolpica-F1 at about 3 per second; finished seasons are cached and never re-downloaded.

## Deploying to GitHub Pages

1. Create an empty repository named `f1-moneyball` on GitHub and push this folder:
   ```bash
   git add -A && git commit -m "Phase 1: foundation"
   git remote add origin https://github.com/<you>/f1-moneyball.git
   git push -u origin main
   ```
2. In **Settings → Pages**, set **Source** to **GitHub Actions**.
3. In **Settings → Actions → General**, allow **Read and write permissions** (the pipeline commits published data).
4. Run **Actions → Data pipeline → Run workflow**. When it succeeds, `Deploy website` publishes the site.

Repository description to use on GitHub: *F1 Moneyball: An Independent Formula 1 Economics & Finance Research Platform.*

## Architecture

```
Jolpica-F1 / FastF1 / manual CSV
   → data/raw (untouched, retrieval log with SHA-256)
   → standardize (team lineage, types) → data/interim (Parquet)
   → validate (errors block publishing) → reports/data_quality.md
   → features (efficiency, HHI, Gini, rank persistence) → data/processed
   → publish (JSON + CSV + manifest + data dictionaries) → website/public/data
   → React site (reads manifest.json first) → GitHub Pages
```

| Path | Purpose |
|---|---|
| `config/` | Sources, study window and regulatory periods, team lineage mapping |
| `src/f1moneyball/` | ingestion, standardization, validation, feature_engineering, publishing, pipeline CLI |
| `data/manual/` | Hand-entered financial observations and regulation events (validated) |
| `config/datasets.yaml` | Registry of every dataset the site expects; the pipeline turns it into `dataset_status.json`, the only source of dataset status for the website |
| `data/metadata/dictionaries.yaml` | Data dictionary for every published dataset (publishing fails if a column is undocumented) |
| `website/` | Vite + React + TypeScript + Tailwind + Plotly |
| `.github/workflows/` | `validation.yml` (PRs), `data_pipeline.yml` (weekly + manual), `deploy.yml` |

## Research integrity rules built into the code

- The website can only show datasets listed in `manifest.json`; missing data shows a "not yet published" state, never placeholder values.
- `is_synthetic_demo` in the manifest forces a red banner on every page if demo data is ever used.
- Financial figures are stored one figure per row with source class (audited / official disclosure / secondary estimate / derived / missing), currency, accounting period, URL and page. Rows without provenance fail validation.
- Every row in the financial CSV must pass validation, so unsourced figures fail the tests.
- Validation errors stop the pipeline before anything is written to the website.

## Disclaimer

F1 Moneyball is an independent research project. It is not affiliated with Formula 1, FIA, Liberty Media or any Formula 1 constructor. Financial estimates and analytical interpretations are identified separately from officially reported figures. Formula 1 and related marks are trademarks of their owners. Sporting data from Jolpica-F1 is used under its terms of use.
