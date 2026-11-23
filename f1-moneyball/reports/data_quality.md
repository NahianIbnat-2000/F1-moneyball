# Data quality report

Errors: 0  
Warnings: 3

| Dataset | Check | Severity | Rows | Message |
|---|---|---|---|---|
| constructor_season | points_reconcile | warning | 37 | Standings points differ from summed race points in seasons [2020, 2021, 2022, 2023, 2024, 2025] (expected where sprint races or penalties apply) |
| financial_observation | period_length | warning | 4 | Accounting periods not about 12 months (not annualised in the data; see robustness check annualised_periods): ['silverstone 2019-08-31 (395 days)', 'silverstone 2020-12-31 (122 days)', 'banbury 2017-06-30 (547 days)', 'leafield 2010-12-31 (457 days)'] |
| financial_observation | accounting_scope_switch | warning | 4 | Teams whose accounts switch between company-only and group-consolidated: ['mclaren', 'mercedes', 'red_bull', 'williams'] (see robustness check scope_control) |
