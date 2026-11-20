# Data quality report

Errors: 0  
Warnings: 4

| Dataset | Check | Severity | Rows | Message |
|---|---|---|---|---|
| constructor_season | points_reconcile | warning | 37 | Standings points differ from summed race points in seasons [2020, 2021, 2022, 2023, 2024, 2025] (expected where sprint races or penalties apply) |
| financial_observation | period_length | warning | 4 | Accounting periods not about 12 months (not annualised in the data; see robustness check annualised_periods): ['silverstone 2019-08-31 (395 days)', 'silverstone 2020-12-31 (122 days)', 'banbury 2017-06-30 (547 days)', 'leafield 2010-12-31 (457 days)'] |
| financial_observation | accounting_scope_switch | warning | 4 | Teams whose accounts switch between company-only and group-consolidated: ['mclaren', 'mercedes', 'red_bull', 'williams'] (see robustness check scope_control) |
| financial_observation | yoy_change | warning | 18 | Year-on-year changes above 50%, to check against the filings: ['banbury staff_costs 2011 (+114%)', 'banbury staff_costs 2012 (+53%)', 'banbury staff_costs 2015 (-58%)', 'banbury staff_costs 2016 (+111%)', 'banbury turnover 2013 (+115%)', 'banbury turnover 2014 (-57%)', 'banbury turnover 2015 (+52%)', 'enstone turnover 2016 (+53%)', 'leafield turnover 2012 (+117%)', 'mclaren staff_costs 2025 (+59%)', 'mclaren turnover 2019 (+50%)', 'mclaren turnover 2020 (+79%)', 'mclaren turnover 2022 (+55%)', 'red_bull staff_costs 2025 (+59%)', 'silverstone staff_costs 2025 (+92%)', 'silverstone turnover 2021 (+148%)', 'williams turnover 2020 (-55%)', 'williams turnover 2021 (+98%)'] |
