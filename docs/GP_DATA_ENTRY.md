# Grand Prix Economy: data entry

Monthly tourism series are not available from one API, so they are entered by hand from
official sources and validated by the pipeline.

## 1. Choose the setting before looking at results
For each host economy, write down in `notes` (first row of each region):
- the series (`arrivals`, `overnight_stays` or `hotel_occupancy`) and why;
- the comparison regions and why they are comparable (similar tourism profile, no Grand Prix,
  same statistical definitions). Choose them before estimating, to avoid picking regions that
  give a convenient answer.

Starting points: Singapore (race since 2008; monthly visitor arrivals from Singapore's official
statistics) and Austria (Spielberg, Styria, back on the calendar in 2014; monthly overnight stays
by federal state from Statistik Austria, with other states as comparison regions).
Record the exact table ID and URL for every series; do not use press figures.

## 2. Enter the series
`data/manual/gp_tourism_monthly.csv`, one row per region, month and series:

| Field | Rule |
|---|---|
| `region_id` | Short ID, e.g. `at_styria` |
| `is_host` | `true` for the host region, `false` for comparison regions |
| `month` | `YYYY-MM` |
| `value`, `unit` | As published. One unit per region and series |
| `source_url`, `table_id`, `retrieval_date` | Required |
| `notes` | Breaks in series, definition changes |

## 3. Enter race dates
`data/manual/gp_race_events.csv`: one row per race, with `race_start_date` (first day of the
weekend), `race_end_date` and a source.

## 4. Validate and publish
```bash
python -m f1moneyball.pipeline validate
python -m f1moneyball.pipeline publish
```
The event study needs 36 months of a host series; the synthetic control needs 24 months before
the first race in the data and at least 3 comparison regions. If the pre-entry fit is poor, the
site flags it and the gap is not read as an effect.
