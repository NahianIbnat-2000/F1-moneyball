# F1 Moneyball 3.0: current-state audit

Date: 23 November 2026. Author: Nahian Ibnat, with Claude (Anthropic) as collaborator.
Source of truth: repository at commit `c33a058`, the deployed site, and the working paper built from that commit.
Earlier audits (`PROJECT_AUDIT.md`, `VERIFICATION_REPORT.md`) were not assumed to still hold; each item below was re-checked.

## 1. Feature verification

| Feature | Evidence checked | Status |
|---|---|---|
| Automated tests | `pytest`: 95 passed | Verified and complete |
| Fixed-effects models | `econometrics/models.py`; re-estimated locally, matches `model_results.csv` | Implemented but needs improvement (finding 1) |
| Wild cluster bootstrap | `econometrics/robustness.py` `wild_cluster_p`: restricted, Webb six-point weights, CR1 t statistic, 9,999 draws, fixed seed, symmetric two-sided p | Implemented but not verified against an independent implementation (Phase C) |
| Robustness checks incl. accounting scope, annualised periods, share-based pay, real terms, Holm | `robustness_checks.csv` rows present | Verified; Holm family is the 6 two-way tests (3 measures × 2 outcomes) |
| Working paper | builds from published data; claim checks in `paper/make_assets.py` | Implemented but needs improvement (finding 2) |
| Points-share outcome | `feature_engineering/sporting.py` line 60: share of **all** constructors' points | Implemented; misdescribed in the paper (finding 2) |
| Provenance explorer, data explorer, Econometrics Lab | pages exist in `website/src/pages`; axe checks passed on 20 Nov | Verified (automated checks only; manual screen-reader test not done) |
| Cost-cap study | `econometrics/cost_cap.py`, robustness rows | Implemented but not re-validated in this audit (Phase D) |
| Grand Prix tourism study | `econometrics/gp_economy.py` | Implemented but not re-validated in this audit (Phase D) |
| Citation metadata | `CITATION.cff` valid; Scholar tags on article page | Verified |
| Live site | hub shows the revised Study 01 finding | Verified |
| GitHub Actions | five workflows present | Implemented but not verified here (no access to run logs from this environment) |
| Raw sporting data | `data/raw` is git-ignored; kept only in a GitHub Actions cache | Blocked for offline replication (finding 4) |
| Financial comparability classification | none per observation; only switch/period warnings | Missing (finding 3) |
| Source-document rights | README paragraph only | Missing (finding 5) |

## 2. Five highest-priority unresolved issues

### Finding 1. Clustered p-values and confidence intervals use the normal distribution (high)

- **Where:** `src/f1moneyball/econometrics/models.py` (`run_models`) and `robustness.py` (`_fit`) call
  `statsmodels ... fit(cov_type="cluster")`, which defaults to `use_t=False`.
- **Evidence:** for staff costs, two-way model: published clustered p = 0.11, CI [−0.043, 0.416].
  With t(G−1 = 7) critical values: p = 0.16, CI [−0.091, 0.463].
- **Why it matters:** with eight clusters, t(G−1) is the standard small-sample choice (Cameron and Miller 2015).
  The published "clustered" numbers are too optimistic. Bootstrap p-values are unaffected.
- **Recommendation:** report clustered inference with t(G−1); keep the bootstrap as the main within-team test.
- **Acceptance:** `model_results.csv` and `robustness_checks.csv` carry t(G−1) p-values and intervals, labelled;
  paper, Lab and article updated; a test asserts `use_t` is on. **Changes published numbers: needs approval.**

### Finding 2. The paper misdescribes the regression outcome (high)

- **Where:** paper Section 3 defines points share "among all covered teams"; the models use the share of
  all constructors' points (`sporting.py` line 60). Table 1, Figure 1 and the efficiency ratio do use the
  covered-team share (`efficiency.py`, `points_share_in_group`).
- **Recommendation:** describe both measures correctly and state which is used where; add the covered-team share
  as a sensitivity outcome (brief 5.1).
- **Acceptance:** the text matches the code; a sensitivity row compares the two outcomes.

### Finding 3. No observation-level comparability classification (high)

- **Where:** `data/manual/financial_observations.csv` has warnings for period length and scope switches,
  but no category per team-season and no restricted-sample estimates.
- **Recommendation:** evidence-based categories (High, Moderate, Limited, Insufficient information) from
  recorded facts; re-estimate on restricted samples; report cluster counts.
- **Acceptance:** `data/manual/comparability.csv` with a reason and source for each classification;
  restricted-sample rows in the robustness table; a report that does not prefer a sample for its p-value.

### Finding 4. Replication depends on a live API and hand-typed website numbers (medium)

- **Where:** `data/raw` is git-ignored; `data_pipeline.yml` restores raw data from an Actions cache.
  Website article numbers are typed in `website/src/lib/articles.ts` with no check against published data.
- **Recommendation:** a replication workflow from committed processed data; a manifest of versions and hashes;
  regression tests linking published coefficients, paper macros and website text.
- **Acceptance:** `replication.yml` runs from a clean checkout; `reproducibility_manifest.json` is produced;
  tests fail if a website or paper number drifts from the published data.

### Finding 5. Redistribution rights of source documents are not assessed (medium)

- **Where:** `data/source_documents` (120 files, 128 MB): Companies House filings, FIA regulations, ONS and
  tourism files. The README says the filings are public records, which is not the same as a right to redistribute.
- **Recommendation:** a rights assessment per category with sources; no deletion without approval.
- **Acceptance:** `docs/SOURCE_RIGHTS.md` with a category and evidence for each source.

## 3. Not issues

- The lag construction (`models.lagged_panel`) correctly skips gaps in a team's accounts.
- The Holm correction is implemented as the standard step-down with monotonicity (`robustness.holm`), and the
  family matches the paper's description.
- The live hub and paper agree on the main findings.
