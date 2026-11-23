# Manual financial data entry

Team finances cannot be collected automatically. This is the documented workflow.

## 1. Find the entity
Search UK Companies House for the operating company (examples to check: the Mercedes team company in Brackley, Red Bull Racing in Milton Keynes, McLaren Racing, Williams Grand Prix Engineering, Aston Martin Lagonda F1 / AMR GP, Alpine Racing (UK), Haas F1 (UK)). Confirm the registration number and that the company actually runs the race team. Write the entity name exactly as registered.

## 2. Open the full accounts
Use the "Filing history" tab. Only full audited accounts count as `audited`. Abbreviated or small-company accounts should be noted in `notes`.

## 3. Enter one row per figure
In `data/manual/financial_observations.csv`:

| Field | Rule |
|---|---|
| `value` | Full units in the original currency (e.g. 361400000, not 361.4) |
| `currency` | ISO code as reported (GBP, EUR, USD). Never convert here |
| `financial_year_start/end` | From the accounts (YYYY-MM-DD) |
| `season_mapped` | The season the period mostly covers. For a calendar year end, the same year. Explain other cases in `notes` |
| `source_class` | `audited` for statutory accounts |
| `source_url`, `document_page` | Direct filing link and the page number of the figure |
| `document_title` | Title of the document as filed (required for any non-missing figure) |
| `transformation` | `none` if copied as reported; otherwise describe the change (e.g. loss shown in brackets entered as negative) |
| `comparability_warning` | Required for secondary and derived estimates. Say why the figure may not compare with other teams or years |
| `confidence` | `high` for audited figures taken directly from the income statement |
| `notes` | Anything that affects comparability: engine activity in the same entity, change in year end, restatements |

Press budget estimates go in as `secondary_estimate`, `low` confidence, with the article URL. They are never mixed with audited figures in the same chart without a visible flag.

## 4. Coverage rule
The dataset shows as **Insufficient coverage** on the site until at least 4 teams have figures in the same season (`min_teams_per_season` in `config/datasets.yaml`). Rows are still downloadable.

## 5. Validate
```bash
python -m f1moneyball.pipeline validate
pytest tests/test_pipeline.py::test_seed_files_validate
```
Open a pull request. CI runs the same checks. A value outside the plausible ranges in `validation/checks.py` fails unless `notes` contains `range_override` plus a reason.
