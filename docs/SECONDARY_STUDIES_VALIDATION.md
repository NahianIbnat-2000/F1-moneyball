# Validation of the cost-cap and Grand Prix tourism studies (F1 Moneyball 3.0, Phase D)

Date: 23 November 2026. Numbers from the published datasets `cost_cap_models`, `competitive_balance`,
`gp_event_study` and `gp_scm_inference`. Nothing in either study was rebuilt; changes are listed in section 3.

## 1. Cost cap

| Item | Finding |
|---|---|
| Outcomes | Five season-level balance measures (normalised HHI, Gini, top-three share, leader's share, rank persistence), computed from all constructors' points. Defined in `feature_engineering/competitive_balance.py`. Sound. |
| Timing | Break at 2021 (financial regulations, FIA 2021 Article 2.3). Specification B adds a 2022 dummy for the technical rules; the 2021 level change is then identified from the single 2021 season. **The cap and the 2022 rules cannot be separated with season-level data**; the study says so. |
| Serial correlation | Newey-West standard errors with one lag on 16 seasons. **Verified problem:** in the placebo years, 14 of 29 tests (48%) give p < 0.05 and 7 give p < 0.01, against about 5% expected. Leaving out the 2014 and 2017 breaks, still 8 of 19. The ITS p-values are far too small and should not be read as significance tests. |
| Placebo years | 2013 to 2018 inside the pre-cap period. **Corrected:** 2014 and 2017 had major technical rule changes, so they are not clean placebos; the published note said "no policy change". The note now says so. The placebo comparison (share of fake breaks at least as large as 2021: 0.6 to 1.0 across measures) is the more reliable guide and already drives the article's conclusion. |
| Power | Smallest level change detectable with 80% power at 5% (2.8 × standard error, new column `mde_80`): 1.0 to 1.7 times the pre-cap standard deviation of each measure (normalised HHI 0.027, leader's share 0.059). Because the standard errors are themselves too small, the true detectable change is larger. Only very large shifts in balance could be seen. |
| Exposure (dose-response) | Pre-cap (2018 to 2020) average turnover or staff costs, six teams, team and season fixed effects, wild bootstrap. Close to zero in every version (bootstrap p 0.85 to 0.99). Six clusters: very low power. |
| Sensitivity to teams and seasons | Without 2020 the post-2021 drops pass p < 0.05; given the 48% placebo rejection rate this is not evidence. Now stated in the article. |
| Conclusion | "No evidence that the cost cap changed competitive balance" is supported as a statement about evidence, not as proof of no effect. The article now adds the detectable-effect statement and that the cap cannot be separated from the 2022 rules. |

## 2. Grand Prix tourism

| Item | Finding |
|---|---|
| Treatment | Austria: the Austrian Grand Prix **returned** to the Red Bull Ring in June 2014 after an absence (a returning race, not a new one); the article says "since F1 returned". Singapore: a new race from September 2008. The two are different interventions and are reported separately, never pooled. |
| Data | Monthly arrivals and overnight stays, nine Austrian federal states 2008 to 2025 (Statistik Austria); Singapore arrivals 2005 to 2025 (Singapore Tourism Board). Regional outcome for Austria, national for Singapore. |
| Pandemic | Both designs end in December 2019 (`gp_economy.ANALYSIS_END`). Verified. |
| Seasonality | Event study uses month-of-year effects and a linear trend. In Styria, race months are +13.3% but the two following months are also up (+7.6%, +6.5%), which a three-day race is unlikely to cause; part of the rise may be summer tourism growing after 2014. Several states without a race also rise in the same months; relative to the rest of Austria the race-month bump is 4.6% (95% CI 1.6% to 7.7%), already in the article. |
| Synthetic control | Pre-entry fit good (RMSPE 0.069 log points for arrivals). Donor weights: Lower Austria 0.32, Salzburg 0.29, Upper Austria 0.20, Vorarlberg 0.10, Tyrol 0.04, Vienna 0.04. Placebo-in-space p = 0.89 (arrivals) and 0.44 (overnight stays). **With nine units the smallest attainable p-value is 1/9 = 0.11**, so the design cannot reach conventional significance; with good-fit placebos only (four units) the minimum is 0.25. |
| Donor pool | All other Austrian states. Spillovers (race visitors staying in neighbouring states) would bias the gap towards zero. Now stated in the article. Donor-selection sensitivity is limited to the good-fit subset already published. |
| Singapore | Only three pre-race years (2005 to 2007) for the September baseline; no comparison countries, so event study only. Race months are 3.4% lower (95% CI −8.3% to +1.7%). The article correctly calls this a lack of evidence, not evidence of no effect. |
| Causal language | Both articles present results as associations or descriptive comparisons. Verified. |

## 3. Changes made

- `econometrics/cost_cap.py`: placebo note flags 2014 and 2017 as rule-change years; new `mde_80` column.
- `website/src/lib/articles.ts`: cost-cap article adds the placebo rejection rate to the "without 2020" result and the
  detectable-effect statement to the conclusion; tourism article adds the post-race months, spillover and minimum
  p-value limitations.
- No published estimate changed.

## 4. Not done, and why

- A placebo-calibrated (randomisation) p-value for the ITS could replace the Newey-West p-values; with six placebo years
  the smallest attainable value is 1/7, so it would not change any conclusion. Recommended only if more seasons are added.
- More host regions were not added (brief: do not add countries to make the dashboard larger).
