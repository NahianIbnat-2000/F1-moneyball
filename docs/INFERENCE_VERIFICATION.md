# Inference verification and sensitivity (F1 Moneyball 3.0, Phases B and C)

Date: 23 November 2026. All numbers below were produced by code in this repository on the published data
(dataset versions as in `website/public/data/manifest.json`). Results are associations, not causal effects.

## 1. Wild cluster bootstrap: independent check (verified)

The project's restricted wild cluster bootstrap (`econometrics/robustness.py`, `wild_cluster_p`) was compared with
`wildboottest` 0.3, the Python port of the R package `fwildclusterboot` (restricted, WCR11, Webb weights, 99,999 draws),
on the six two-way tests (three resources × two outcomes).

| Resource | Outcome | This project (9,999 draws) | wildboottest, Webb | wildboottest, Rademacher |
|---|---|---|---|---|
| Turnover | Points share | 0.149 | 0.152 | 0.141 |
| Turnover | Position | 0.055 | 0.055 | 0.078 |
| Staff costs | Points share | 0.042 | 0.041 | 0.039 |
| Staff costs | Position | 0.013 | 0.012 | 0.000 |
| Headcount | Points share | 0.252 | 0.252 | 0.281 |
| Headcount | Position | 0.046 | 0.045 | 0.047 |

The largest difference with the same weights is 0.003, within simulation error (standard error about 0.004 at
9,999 draws). Implementation checked: null imposed; Webb six-point weights; clusters = team lineage; CR1 t statistic
with G/(G−1)·(N−1)/(N−K); symmetric two-sided p-value; fixed seed 20261119. With eight clusters Rademacher weights allow
only 2^8 = 256 distinct draws and give a degenerate p = 0.000 in one case, which supports the choice of Webb weights.

## 2. Confidence intervals (new; changes what should be reported)

The published 95% intervals are clustered intervals with **normal** critical values (`statsmodels` default
`use_t=False`), while the within-team p-values come from the bootstrap. The two can disagree: for staff costs and points
share the published interval includes zero although the bootstrap p-value is 0.042.

New code (`econometrics/inference.py`) computes intervals by inverting the same bootstrap test. At β = 0 it reproduces
every published bootstrap p-value exactly (tested).

| Resource | Outcome | Coefficient | Normal CI (published) | t(7) CI | Bootstrap CI | Bootstrap p |
|---|---|---|---|---|---|---|
| Turnover | Points share | 0.048 | [−0.010, 0.105] | [−0.021, 0.117] | [−0.033, 0.121] | 0.149 |
| Turnover | Position | −1.513 | [−2.825, −0.202] | [−3.095, 0.069] | [−4.088, 0.025] | 0.055 |
| Staff costs | Points share | 0.186 | [−0.043, 0.416] | [−0.091, 0.463] | [0.002, 0.493] | 0.042 |
| Staff costs | Position | −4.472 | [−7.954, −0.990] | [−8.673, −0.271] | [−9.263, −1.822] | 0.013 |
| Headcount | Points share | 0.088 | [−0.076, 0.251] | [−0.110, 0.285] | [−0.008, 0.508] | 0.252 |
| Headcount | Position | −3.281 | [−6.337, −0.226] | [−6.967, 0.405] | [−11.069, −0.159] | 0.046 |

Bootstrap intervals are asymmetric and mostly wider than the normal ones. Clustered p-values with t(G−1) (`p_t`) are
larger than the published normal ones: staff costs and points share 0.16 instead of 0.11; staff costs and position
0.040 instead of 0.012. **Recommendation (needs approval):** report bootstrap intervals with bootstrap p-values in the
paper and the Lab, and label the clustered ones as t(G−1).

## 3. Multiple testing (verified)

The Holm family is the six two-way tests above: three resources × two outcomes, all treated as primary. The adjustment is
the standard step-down with monotonicity. No member is significant at 5% after adjustment (smallest 0.078). The checks in
sections 4 and 5 are sensitivity analyses and are not part of the family; they are not used to claim significance.

## 4. Financial comparability (Phase B, new)

Classification rules are in `econometrics/comparability.py`; every category is derived from facts recorded from the
filings and comes with its reasons and source (dataset `financial_comparability`). Turnover: 89 High, 3 Moderate,
12 Limited, 2 Insufficient information.

| Two-way model, staff costs | Points share (boot p) | Position (boot p) | Team-seasons | Teams |
|---|---|---|---|---|
| Full sample (published) | 0.186 (0.042) | −4.47 (0.013) | 95 | 8 |
| Lagged resource of high comparability | 0.181 (0.117) | −4.07 (0.010) | 83 | 7 |
| High or moderate | 0.182 (0.115) | −4.14 (0.010) | 84 | 7 |
| Team-by-accounting-basis fixed effects | 0.171 (0.101) | −4.32 (0.027) | 95 | 8 |

Direction and size are stable. The restricted samples lose one team (Caterham's partial accounts) and 11 to 12
team-seasons; with seven clusters the bootstrap becomes even coarser, so their p-values are not treated as better
evidence. For turnover the restricted estimates are larger (0.072 against 0.048, boot p about 0.08 to 0.10).

## 5. Alternative outcomes and timing (new)

| Two-way model | Staff costs (boot p) | Turnover (boot p) |
|---|---|---|
| Points share of all constructors (published outcome) | 0.186 (0.042) | 0.048 (0.149) |
| Points share among covered teams only | 0.265 (0.042) | 0.069 (0.158) |
| Normalised position (0 champion, 1 last) | −0.455 (0.014) | −0.172 (0.079) |
| Resource lagged two seasons | 0.141 (0.065) | 0.016 (0.52) |
| Reverse: log resource on last season's points share | 0.85 (0.23) | 1.74 (0.074; clustered p < 0.001) |

The published regressions use the share of **all** constructors' points (`feature_engineering/sporting.py`), while
Table 1, Figure 1 and the efficiency ratio use the share among covered teams; the paper's Data section described only the
latter and has been corrected. Uncovered teams took 12% (2014) to 35% (2018) of each season's points. The covered-team
outcome gives larger coefficients with the same bootstrap p-values.

The reverse-direction check matters for interpretation: turnover follows last season's points at least as strongly as
points follow last season's turnover, consistent with prize money paid by results. Staff costs show a weaker reverse
pattern, which supports treating staff costs as the more informative resource. None of this identifies cause.

Fractional-response models (e.g. fractional logit) suit bounded shares, but with eight clusters, team and season fixed
effects and few observations near the bounds (only Manor and Caterham near zero), they add little beyond the linear
model and the normalised-position check; not implemented.

## 6. Efficiency ratio (audit)

The ratio is points share among covered teams divided by turnover share. Its denominator depends on which teams report
in a season (5 to 8 teams), so a team's ratio can change when another team's accounts are missing, as in 2017 and 2018.
It is unstable for small teams (coefficient of variation 1.3 for Williams, 1.9 for Manor) and zero for teams that score
no points. It describes points relative to money; it does not measure efficiency in an economic sense.
**Recommendation (needs approval):** relabel it as the "points-to-turnover-share ratio" on the site and in the paper,
keeping the column name `efficiency_ratio` for reproducibility. A model-based benchmark is not added: with eight teams the
residuals would carry wide uncertainty and could be misread as managerial quality.

## 7. Approvals needed before published numbers or wording change

1. Report bootstrap intervals with bootstrap p-values; label clustered inference as t(G−1).
2. Relabel the efficiency ratio.
3. Add the reverse-direction and covered-share results to the paper's robustness section.

## Addendum (23 November 2026): exact ties across computers

The Replication workflow found 9 bootstrap p-values that differed by 1/9,999 between GitHub's machine and the build
environment. Cause: with Webb weights, a draw that gives every cluster the same weight leaves |t*| = |t| exactly (the t
statistic is unchanged when residuals are rescaled); with 6 or 7 clusters this happens about once per 9,999 draws, and
floating-point rounding decided whether it was counted. Diagnosed by counting near-ties in every bootstrap call: 16 of
66 calls had exactly one (the 7-team restricted samples and the 6-team cost-cap models); none of the 8-team models did.
Fix: `at_least_as_extreme()` in `inference.py` compares with a relative tolerance of 1e-9, so ties always count, as the
p-value definition requires. Test: `test_constant_weight_draw_counts_as_tie`.
