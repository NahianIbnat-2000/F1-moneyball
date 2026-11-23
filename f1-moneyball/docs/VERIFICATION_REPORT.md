# F1 Moneyball 2.0: verification report

Date: 20 November 2026. Author: Nahian Ibnat, with Claude (Anthropic) as collaborator.
Companion to `docs/PROJECT_AUDIT.md`, which lists the findings (C1, H1 and so on) referred to below.

Every number in this report comes from the published datasets or from a check run on the date above.
Each item is in one of four groups: **tested**, **done but not tested**, **proposed** (needs a decision) or **blocked**.

## 1. Tested

| Item | What was checked | Result |
|---|---|---|
| Accounting-scope control (C1) | Re-estimation with a group-accounts indicator; published in `robustness_checks` (`scope_control`, `scope_control_position`) | Staff costs → points share 0.184 (main 0.186), bootstrap p 0.11 (main 0.04). Staff costs → position −4.59, bootstrap p 0.02. |
| Annualised periods (H1) | `annualised_periods` check; unit tests on day counts and scaling | Staff costs 0.182, bootstrap p 0.048 |
| Share-based pay | `staff_costs_ex_share_based_pay` check; unit test | Staff costs 0.166, bootstrap p 0.044 |
| Holm adjustment (H2) | `holm_adjusted` rows; unit tests on the step-down order and the 6-test family | Smallest adjusted p 0.078 (staff costs → position); others 0.21 to 0.30 |
| Validation warnings (H4) | Period length, scope switch, year-on-year changes; unit tests | Pipeline: 0 errors, 3 warnings (one older warning on sprint points plus two comparability warnings) |
| Large year-on-year changes | OCR of the stated page of the saved filing for all 18 flagged changes, both years (`scripts/verify_large_changes.py`) | 36 of 36 figures found; no figure changed. Record in `data/manual/verified_large_changes.csv`; the warning returns if either value changes |
| 2025 jumps | Red Bull and AMR staff costs read from the page images; McLaren share-based pay | Figures correct as recorded |
| Paper | Built from published data; claim checks stop the build if a sentence no longer matches the data | Builds with no LaTeX warnings, 13 pages. Abstract revised with author approval |
| Python tests | `pytest` | 95 passed |
| Lint | `ruff check src tests scripts` | No issues |
| Website build | TypeScript check and production build | Passes |
| Phone layout | Page width measured at 390 px on every page | No page wider than the screen (Moneyball page fixed) |
| Accessibility (M6) | axe-core, WCAG 2.1 A/AA plus best practices, 15 pages at 1280 px and 390 px (`website/scripts/a11y.mjs`) | No violations, after fixing heading order, keyboard access to scrolling tables, and labels in the provenance grid |
| Google Scholar tags (M3) | Built article page inspected | Title, author, dates and PDF link present; only on the page with a paper |
| CITATION.cff (M3) | `cffconvert --validate` | Valid (schema 1.2.0) |
| Real terms (H3) | ONS D7BT downloaded by the author (release of 18 November 2026); yearly values 2010–2025 checked against the mean of the monthly values in the same file (all within rounding); raw download kept in `data/source_documents/ons` | Team-effects staff-cost estimate 0.058 in 2015 pounds (0.034 nominal), bootstrap p 0.40; two-way model unchanged by construction. Appears in the published results after the next Data pipeline run |
| Provenance links | Every "saved copy" link checked against the repository | 105 of 105 files exist |

## 2. Done but not tested

| Item | Why not tested |
|---|---|
| Accessibility workflow in GitHub Actions (`.github/workflows/accessibility.yml`) | Runs for the first time on the next push. The same script passes locally. |
| `requirements-lock.txt` | Versions are the ones the tests passed with locally on Python 3.13. The GitHub workflows still use Python 3.12 and the looser `requirements.txt`; they were not switched, so the published results do not change. |
| Keyboard and screen-reader use | Automated checks find only part of the possible problems. No test with a real screen reader was done. |
| Google Scholar indexing | Tags are correct, but whether and when Scholar indexes the page cannot be tested from here. |

## 3. Proposed (needs a decision)

| Item | Note |
|---|---|
| Source PDFs in the repository (M4) | 120 filings, about 128 MB. They are public Companies House records, but the basis for redistributing them is not written down, and the repository grows with each filing. Options: document the basis, move them to Git LFS, or link to Companies House only. |
| Old session reports in `docs/` (M2) | They read as history. Suggest a short note pointing to `PROJECT_AUDIT.md` and this report as current. |
| Switch CI to the lock file | Would make every run use the exact package versions. Small risk that results change in the last decimal; check before switching. |
| Tagline (L2) | The brief suggests "The Economics of Speed"; the site uses "The Economics Behind the Speed". Not changed. |
| Full redesign (L3) | Not done. The current design already matches the brief's direction. |

## 4. Blocked

| Item | Blocker | What unblocks it |
|---|---|---|
| SSRN revision | Needs the author's SSRN login | Upload the current PDF from the website as a revision of paper 7730805. |

## 5. What changed in the conclusions

With the author's approval, the paper and the web article now say that the within-team evidence is clearest for staff
costs and championship position, that the points-share estimate becomes less certain once accounting scope is controlled
for, and that no within-team result survives a correction for multiple testing at 5%. All results are still described as
associations, not causal effects. The changelog (`data/manual/changelog.yaml`) records these changes.

## 6. Files added or changed in this work

- Econometrics: `src/f1moneyball/econometrics/robustness.py`, `src/f1moneyball/pipeline.py`
- Validation: `src/f1moneyball/validation/checks.py`, `scripts/verify_large_changes.py`, `data/manual/verified_large_changes.csv`
- Tests: `tests/test_comparability.py`
- Paper: `paper/main.tex`, `paper/make_assets.py`, `paper/references.bib`
- Website: `website/src/pages/Lab.tsx`, `website/src/pages/Provenance.tsx`, layout and table components, `website/scripts/prerender-head.ts`, `website/scripts/a11y.mjs`
- CI: `.github/workflows/accessibility.yml`
- Documentation: `docs/PROJECT_AUDIT.md`, `docs/REAL_TERMS.md`, this report, `CITATION.cff`, `requirements-lock.txt`, `data/manual/changelog.yaml`
