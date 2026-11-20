# Real-terms money measures

The financial data are in nominal pounds, exactly as filed. To also report results in constant prices, the
pipeline deflates turnover and staff costs by the UK Consumer Prices Index.

## What it changes, and what it cannot

- **Two-way fixed effects (team and season): no change, by construction.** The price index is the same for
  every team in a season, so the season effect absorbs it. A test (`test_real_terms_cannot_change_two_way_model`)
  checks this.
- **Pooled and team-only models:** these can change, because they compare years with different price levels.
  They are reported as the robustness check `real_terms`.
- Headcount is a number of people and is never deflated.

## The source file

The build environment cannot reach ons.gov.uk, so the index is added by hand, once a year.

1. Open the ONS series **CPI INDEX 00: ALL ITEMS 2015=100**, series ID **D7BT**:
   https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23
2. Click **Download → CSV**.
3. From the yearly rows only (lines like `"2015","100.0"`), create `data/manual/uk_cpi_annual.csv`:

```
year,cpi_index,source_url,retrieved
2010,...,https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23,YYYY-MM-DD
2011,...,https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23,YYYY-MM-DD
```

   Copy the numbers exactly as ONS gives them. Do not round or edit them.
4. Commit the file and run the Data pipeline. The `real_terms` rows appear in `robustness_checks`.

Until the file exists, the pipeline logs "real-terms checks skipped" and publishes everything else as normal.

## Why CPI and not a sector index

There is no official price index for F1 team costs. CPI measures general UK prices, which is the right
yardstick for "how much buying power did this money have". It does not capture wage growth for engineers, which
probably rose faster, so real-terms staff costs are a conservative measure.
