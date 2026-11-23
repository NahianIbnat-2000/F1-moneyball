# F1 Moneyball 3.0: implementation, verification and publication-readiness report

Date: 23 November 2026. Author: Nahian Ibnat, with Claude (Anthropic) as collaborator.
Companion documents: `F1_MONEYBALL_3_AUDIT.md` (Phase A), `INFERENCE_VERIFICATION.md` (Phases B and C),
`SECONDARY_STUDIES_VALIDATION.md` (Phase D), `REPLICATION.md` and `SOURCE_RIGHTS.md` (Phase E).

## 1. Verified findings (unchanged by this work)

- Between teams, money share and points share are strongly associated (correlation 0.78; pooled turnover coefficient 0.083).
- Within teams, the clearest association is staff costs with championship position (−4.47, bootstrap p = 0.013).
- No within-team result survives the Holm correction (smallest adjusted p = 0.078).
- The wild cluster bootstrap matches an independent implementation (`wildboottest`) within simulation error.
- No published estimate changed. A clean rebuild reproduces all published datasets exactly (see section 4).

## 2. New findings

1. Published clustered p-values and intervals use normal critical values; with eight clusters t(G−1) gives larger
   p-values (staff costs and points share 0.16 instead of 0.11). Now published as `p_t`, alongside.
2. Bootstrap intervals by test inversion are now available and agree with the bootstrap p-values; the published normal
   intervals do not (staff costs and points share: normal [−0.043, 0.416], bootstrap [0.002, 0.493]).
3. The regressions use the share of **all** constructors' points; the paper described the covered-team share. Corrected.
4. Financial comparability: 89 of 106 turnover observations are High, 3 Moderate, 12 Limited, 2 Insufficient
   information. Restricting to comparable accounts keeps the direction and size of the main estimates.
5. Reverse direction: turnover follows last season's points at least as strongly as the reverse (consistent with prize
   money); staff costs much less so.
6. Cost cap: the interrupted-time-series p-values reject in 48% of placebo years, so they overstate significance; the
   placebo comparison is the reliable guide. Detectable change is 1 to 1.7 pre-cap standard deviations.
7. Tourism: the synthetic control cannot reach p below 0.11 with nine units; race-month rises in Styria extend to the
   following two months, suggesting part is a summer trend.
8. Reproducibility bug fixed: `publish` from a clean checkout used stale processed files and produced different results
   (63 instead of 95 observations) without warning. It now rebuilds the analysis tables.
9. Rights: Jolpica-derived data are CC BY-NC-SA 4.0; FIA PDFs are restricted; Companies House filings' copyright belongs
   to the filing companies.

## 3. Peer-review-style assessment of the working paper

| Area | Assessment |
|---|---|
| Originality and contribution | The traceable, audited panel is the clearest contribution and is verifiable (every figure has a filing and page; the 18 large changes were checked against the filings). The novelty sentence is hedged ("to my knowledge") and should stay so. |
| Strongest claim | "Staff spending goes with a better championship position" is supported by the bootstrap and by the comparability checks, but not after the Holm correction, and it is an association. The paper says this; keep it as suggestive. |
| Points-share result | Sensitive to accounting scope and to the inference method; correctly described as less certain. |
| Inference reporting | Needs the change in section 5, item 1: intervals and p-values from the same procedure. |
| Identification | No causal claim is made. The reverse-direction result should be added to the discussion because it directly supports the paper's caution for turnover. |
| External validity | UK-registered teams only (about 65% to 88% of each season's points). Stated. |
| Cost cap | Conclusion worded as lack of evidence; now also states the detectable effect size. |
| Clarity | Full prose with definitions after the 22 November revision. |

## 4. Tests and replication

- Python tests: 110 passed, 1 skipped (the bootstrap-interval test runs once the next pipeline run publishes the intervals).
- Lint: no issues (`ruff check src tests scripts`).
- Clean-copy rebuild compared with the published reference: all 16 datasets match; robustness adds 30 rows (restricted
  samples, alternative outcomes, reverse direction); three raw-only pit-stop columns reported, not rebuilt.
- Bootstrap: identical p-values from the new vectorised code at β = 0 for all six main tests; independent package within 0.003.
- **Not run here:** the new GitHub workflow `replication.yml` (runs on the next push); the LaTeX step inside it uses the
  same action as the existing paper workflow. Manual screen-reader testing and performance measurements (LCP, INP) were
  not done; automated accessibility checks passed on 20 November.

## 4b. Website consistency (Phase F)

- Article, hub and paper quote the same coefficients and sample sizes; this is now enforced by
  `tests/test_published_consistency.py`, so a future rebuild that moves a number fails the tests.
- Cost-cap and tourism articles now state the placebo over-rejection, the detectable effect and the 1/9 p-value floor.
- Still inconsistent until approval 5.1: the article and the Lab show normal-based intervals (staff costs and points
  share: −0.043 to 0.416) while the bootstrap interval is 0.002 to 0.493. Same for "efficiency ratio" naming (5.2).

## 5. Changes that needed approval (approved 23 November 2026; implemented in version 3.1, see section 8)

1. Report bootstrap intervals with bootstrap p-values in the paper (Table 2), the Lab and the article; label clustered
   inference as t(G−1). This changes published intervals and clustered p-values, not the coefficients or bootstrap p-values.
2. Relabel the "efficiency ratio" as the "points-to-turnover-share ratio" on the site and in the paper.
3. Add the reverse-direction and restricted-sample results to the paper's robustness section.
4. Source documents: replace the 9 FIA PDFs with a hash manifest; decide on the 105 Companies House filings
   (`SOURCE_RIGHTS.md`, section 3).
5. Show dataset licences in the data explorer.

## 6. Publication readiness

| Criterion | Status |
|---|---|
| Research contribution | Clear for a working paper: traceable data plus a careful between/within separation. |
| Data quality | High for the covered teams; comparability documented per observation. |
| Econometric defensibility | Good once item 5.1 is applied; few-cluster limits stated. |
| Replication | Complete from committed inputs; raw API pull documented as the one external dependency. |
| Citation accuracy | References checked against sources during the November revisions; new references in this phase are standard works. |
| Ethics and licensing | No personal data. Licensing issues identified (section 2, item 9) with recommendations. |
| Status | Working paper, not peer reviewed; submitted to SSRN (revision pending). No DOI yet. |

Realistic dissemination paths, without any promise of acceptance: the SSRN working paper; a GitHub release archived on
Zenodo to obtain a DOI for the code and data; and, after the items in section 5, submission to a field journal such as
the Journal of Sports Economics or the International Journal of Sport Finance, where small-sample panel studies of
team finances are within scope.

## 7. Release package (prepared, not published)

A versioned release (suggested tag `v1.1-working-paper`) should contain: the PDF, `docs/REPLICATION.md`, the published
datasets in `website/public/data` with their licences, the code, `requirements-lock.txt` and `pyproject.toml`, the
appendices (inside the paper), `CITATION.cff`, and `data/manual/changelog.yaml` as version history. Creating the GitHub
release and the Zenodo deposit needs the author's accounts.

## 8. Version 3.1: approved changes (branch `moneyball-3.1-approved`, not deployed)

Verified before implementation:
- t(G−1) p-values recomputed independently from coefficient and standard error (maximum difference 2e-16).
- Bootstrap intervals: the bootstrap p-value at each endpoint is 0.050; a different seed moves the staff-cost interval
  from [0.0017, 0.4925] to [0.0020, 0.4938]. Model table and robustness table bootstraps are identical.
- Licences checked on the publishers' pages (Jolpica TERMS.md, Statistik Austria open data, data.gov.sg Open Data
  Licence, ONS terms, FIA website terms PDF, Companies House public-task copyright page).
- Each of the nine FIA links opened and showed the same title, issue and date as the local copy.

| Item | Status |
|---|---|
| 1. t(G−1) clustered inference and bootstrap intervals in paper, Lab, article, Moneyball page | Done. Coefficients and bootstrap p-values unchanged. |
| 2. Rename to points-to-resource-share ratio (points-to-turnover-share for turnover) | Done, with equation and definition in the paper; column renamed, file name kept. Bug fixed: Lab comparison mixed three measures. |
| 3. Restricted-sample, alternative-outcome, timing and reverse-direction results in the paper | Done: new Table 4 with N, teams, bootstrap intervals, both p-values; text in Section 6, limitations in Sections 7 and 8. |
| 4. Source documents | FIA: removed from current files, links and hashes recorded. Companies House: kept until the **Source documents** workflow confirms each link by hash. |
| 5. Licences in the Data Explorer | Done for every dataset; unknown or unverified terms are labelled. |

Results that changed in wording (not in value): the clustered p-value for staff costs and points share is 0.16 (was
0.11 with the normal distribution); the staff-cost bootstrap interval just excludes zero, so the statement "every
within-team interval includes zero" now applies to clustered intervals only. New result: turnover follows last
season's points (clustered p = 0.01, bootstrap p = 0.07).

Tests: 125 passed against the rebuilt data (115 passed and 10 skipped against the data currently on main, because the
new columns appear only after the pipeline runs). Paper compiles with no undefined references or overfull lines; 368
generated numbers, all claim checks pass.

Not done here, and why: the rebuilt datasets are not committed, because the build environment cannot recreate three
raw-only pit-stop columns; the **Data pipeline** workflow must be run on the branch. Byte-level hash checks of the
official links need the **Source documents** workflow. The other two studies were outside the
approved scope and keep their existing inference. The cost-cap dose-response model and its event study use standard
errors clustered by team with few teams, so the same t(G−1) and bootstrap treatment is recommended there next.
