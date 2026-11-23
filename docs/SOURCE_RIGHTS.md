# Source documents and data: redistribution rights

Date: 23 November 2026 (updated for version 3.1 the same day). This is a reading of each source's published terms,
not legal advice. Public accessibility is not treated as a right to redistribute. The machine-readable version of this
table is the `rights` block of each source in `config/sources.yaml`; the Data Explorer shows it for every dataset.

## 1. Assessment by source

| Source | Files in this repository | Terms found | Category |
|---|---|---|---|
| Jolpica-F1 API (race data) | none (raw pull is git-ignored); derived tables in `data/processed` and published datasets `constructor_season`, `race_result`, `pit_stop`, `competitive_balance` | Data licensed CC BY-NC-SA 4.0; free for non-commercial use ([TERMS.md](https://github.com/jolpica/jolpica-f1/blob/main/TERMS.md)) | Redistributable subject to conditions: attribution, non-commercial, **share-alike** (adapted data must carry the same licence) |
| Statistik Austria (tourism) | `data/source_documents/statistik_austria` (4 OGD files) | Open data licensed CC BY 4.0 ([data.statistik.gv.at](https://data.statistik.gv.at/web/)) | Openly licensed (attribution) |
| Singapore Tourism Board via data.gov.sg | `data/source_documents/singapore_stb` (2 files) | Singapore Open Data Licence v1.0: notice "Contains information from {dataset} accessed on {date}", no suggestion of official status or endorsement ([licence](https://data.gov.sg/open-data-licence)) | Openly licensed (attribution) |
| ONS (CPI, D7BT) | `data/source_documents/ons` (1 file) | Most ONS content is Crown copyright published under the Open Government Licence ([ONS terms](https://www.ons.gov.uk/help/terms-conditions)); OGL v3.0 requires attribution | Openly licensed (attribution) |
| FIA regulations | none since version 3.1 (9 PDFs listed with links and hashes) | Copyright vests exclusively in the FIA; use subject to prior written consent; extracts may be quoted with the source; downloads and reproduction for personal non-commercial use only ([FIA website terms](https://www.fia.com/sites/default/files/basicpage/file/Terms%20and%20Conditions%20FIA%20Website.pdf), clauses 2.4 and 2.9) | **Restricted**: linked, not hosted |
| Companies House filings | none since version 3.1 (105 PDFs listed with links and hashes) | Register made available under section 47 of the Copyright, Designs and Patents Act 1988; copyright in filed documents belongs to the filing company; Companies House does not license them under the OGL and imposes no rules on use of register information ([gov.uk](https://www.gov.uk/government/publications/companies-house-accreditation-to-information-fair-traders-scheme/public-task-copyright-and-crown-copyright)) | **Rights unclear** for republishing whole filings; extracted figures (facts) with citations are not affected |

## 2. What this means for the project

- **Published Jolpica-derived datasets** must state CC BY-NC-SA 4.0 and credit Jolpica-F1. The repository `LICENSE` already
  says datasets keep their sources' licences; the licence is now recorded in `config/sources.yaml`. The project is
  non-commercial, which the licence requires.
- **Model outputs and the paper** report the project's own analysis. They cite their sources; share-alike is applied
  conservatively to datasets that contain Jolpica-derived rows.
- **Hand-entered financial figures** (`financial_observations.csv`) are facts with page references; publishing them with
  citations is not affected by the filings' copyright.

## 3. What was done in version 3.1 (approved by Nahian Ibnat, 23 November 2026)

1. **FIA PDFs (9 files): removed from the repository's current files** and listed in
   `data/metadata/source_documents.csv` with title, official link and the SHA-256 hash of the copy that was used. Each
   link was opened on 23 November 2026 and its title, issue and date match the copy. A byte-level hash comparison could
   not be run from the build environment (no network access to fia.com); the **Source documents** workflow does it.
   The old copies remain in the git history: removing them from history would be irreversible and was not done.
2. **Companies House filings (105 files): kept for now.** Document-level links exist (for example
   `.../company/01806337/filing-history/<transaction id>/document?format=pdf`), but they could not be resolved and checked
   from the build environment. The **Source documents** workflow finds each filing's link from the public filing
   history, downloads it and compares its hash with the local copy. A copy is removed only where the hashes match and
   after review. Where Companies House serves a file whose bytes differ from the saved copy (for example a re-rendered
   PDF), the copy stays and the difference is reported, because the hash would no longer prove which file was used.
3. **Data Explorer:** every dataset shows the licence, required attribution and restrictions of each source, with the
   date checked and a link to the terms. Missing terms are shown as "Unknown" and unchecked ones as "Not verified".
4. **Source list corrected:** "national statistics" split into Statistik Austria, the Singapore Tourism Board and ONS;
   OpenF1 removed from the pit-stop dataset (no code uses it).

Effect on reproducibility: no model reads the PDFs. `scripts/verify_large_changes.py` and the provenance explorer use
the Companies House copies, which are still present. The FIA documents were used only to verify the regulation events,
which cite document, issue and article; they can be downloaded from the links in the manifest and checked by hash.

## 4. Companies House filings: links instead of copies (approved by Nahian Ibnat, 23 November 2026)

The **Source documents** workflow downloaded each filing from Companies House and compared SHA-256 hashes.

| Result | Filings | What was done |
|---|---|---|
| Official file identical to the copy used | 91 | Copy removed; manifest records the official link, hash and `verified` |
| No link found by the automated reader | 14 | Candidate links then found by reading the public filing history by hand; not yet compared by hash. Copies moved to the author's private archive and removed from the repository; manifest records `candidate_unverified`, the link and the reason |

The 14: Williams 2010 to 2019 (the reader returned no link; cause not established), Force India 2012 (same), and
Caterham 2010 to 2012 (the company was dissolved after liquidation in 2020; the first page of its filing history holds
only insolvency filings and the reader stopped there; fixed in `scripts/source_documents.py`). Their 70 financial
figures (14 filings × 5 measures) are kept and flagged (`source_document_status` in `financial_observation`).

Sensitivity: the robustness rows `exclude_unverified_sources_*` re-estimate the two-way models without those figures
(81 of 95 team-seasons, 7 of 8 teams). Staff costs: 0.202 for points share (bootstrap p = 0.084; main estimate 0.186,
p = 0.042) and −4.50 places for position (bootstrap p = 0.047; main −4.47, p = 0.013). The estimates barely move; the
uncertainty grows, as in the other restricted samples. No conclusion changes.

Not done: no git history was rewritten and no original file was deleted permanently. The copies remain in earlier
commits and in the private archive. Next step: run the **Source documents** workflow again; where a candidate link's
hash matches, its status becomes `verified` and the sensitivity rows for it disappear automatically.
