# Replicating F1 Moneyball

## What a clean checkout can reproduce

Everything from the committed inputs onward: every published dataset, every model and robustness estimate, the
paper's numbers, tables and figures, the PDF and the website. The GitHub workflow **Replication**
(`.github/workflows/replication.yml`) runs all of it on a fresh machine and fails if any published number moves.

Inputs it uses:

| Input | Where | Origin |
|---|---|---|
| Financial figures | `data/manual/financial_observations.csv` | Entered by hand from Companies House filings, with page references |
| Regulation events, tourism series, race dates, CPI | `data/manual/*.csv` | Official sources listed in `config/sources.yaml` |
| Sporting tables | `data/processed/constructor_season.parquet`, `race_result.parquet`, `qualifying.parquet` | Built from the Jolpica-F1 API |

## What needs network access

The raw Jolpica-F1 pull (`python -m f1moneyball.pipeline ingest`) is git-ignored and needs the API. Without it, the
committed sporting tables are used. Three pit-stop columns of `constructor_season` (`median_pit_gap_s`, `pit_races`,
`service_pit_stops`) can only be rebuilt from the raw pull; no model uses them, and the comparison script reports them.

## Steps (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-lock.txt          # exact versions tested (Python 3.13); or: pip install -e ".[dev]"
pytest -q                                      # unit tests and research regression tests
python -m f1moneyball.pipeline publish         # validates inputs, rebuilds every published dataset
python scripts/compare_published.py            # compares with the published copies in git (exit 1 on any difference)
python paper/make_assets.py                    # paper numbers, tables, figures (needs matplotlib)
cd paper && latexmk -pdf main.tex && cd ..     # the paper (needs TeX Live with biber)
cd website && npm ci && npm run build && cd .. # the website
python scripts/repro_manifest.py               # reproducibility_manifest.json
```

## Source documents

`data/metadata/source_documents.csv` lists every document a figure was read from, with its official link and SHA-256
hash, its verification status and the observations read from it. Filings are not stored in the repository: download
one from its `document_url` and compare its SHA-256 with the manifest. `python scripts/source_documents.py check`
confirms that the manifest is complete and that the open-data inputs kept in the repository match their hashes (this runs
in the tests). The workflow **Source documents** downloads every official link and compares hashes. The pipeline and the
models do not read the PDFs; `scripts/verify_large_changes.py` downloads the filings it needs and checks their hashes.

## Determinism

The wild cluster bootstrap uses a fixed seed (20261119) and 9,999 draws, so every p-value and bootstrap interval is
identical on every run. `reproducibility_manifest.json` separates deterministic content (input and output hashes,
dataset versions, settings, package versions) from what is expected to vary (build time, machine, PDF bytes).

## Approved results

`data/metadata/reference_results.json` holds the approved headline results. `tests/test_published_consistency.py`
fails if the published data, the website article or the research hub drift from them. Changing a reference value is
a deliberate step that should be reviewed and recorded in `data/manual/changelog.yaml`.
