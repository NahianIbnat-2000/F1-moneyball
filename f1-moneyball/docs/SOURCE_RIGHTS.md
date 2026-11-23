# Source documents and data: redistribution rights

Date: 23 November 2026. This is a reading of each source's published terms, not legal advice.
Public accessibility is not treated as a right to redistribute. **No file has been removed or moved**; the
recommendations in section 3 need the author's approval.

## 1. Assessment by source

| Source | Files in this repository | Terms found | Category |
|---|---|---|---|
| Jolpica-F1 API (race data) | none (raw pull is git-ignored); derived tables in `data/processed` and published datasets `constructor_season`, `race_result`, `pit_stop`, `competitive_balance` | Data licensed CC BY-NC-SA 4.0; free for non-commercial use ([TERMS.md](https://github.com/jolpica/jolpica-f1/blob/main/TERMS.md)) | Redistributable subject to conditions: attribution, non-commercial, **share-alike** (adapted data must carry the same licence) |
| Statistik Austria (tourism) | `data/source_documents/statistik_austria` (4 OGD files) | Open data licensed CC BY 4.0 ([data.statistik.gv.at](https://data.statistik.gv.at/web/)) | Openly licensed (attribution) |
| Singapore Tourism Board via data.gov.sg | `data/source_documents/singapore_stb` (2 files) | "Free forever for personal or commercial use, under the Open Data Licence" ([data.gov.sg](https://data.gov.sg/datasets/d_33796e0e35e57890bdd6aa34364b898d/view)) | Openly licensed (attribution) |
| ONS (CPI, D7BT) | `data/source_documents/ons` (1 file) | ONS statistics are published under the Open Government Licence v3.0; to be confirmed on the ONS terms page | Openly licensed (attribution), pending confirmation |
| FIA regulations | `data/source_documents/fia` (9 PDFs) | Copyright vests exclusively in the FIA; use subject to prior written consent; extracts may be quoted with the source; downloads and reproduction for personal non-commercial use only (FIA website terms, clauses 2.4 and 2.9) | **Restricted**: public hosting of full PDFs is not covered |
| Companies House filings | `data/source_documents/<team>` (105 PDFs, about 128 MB with the above) | Register made available under section 47 of the Copyright, Designs and Patents Act 1988; copyright in filed documents belongs to the filing company; Companies House does not license them under the OGL and imposes no rules on use of register information ([gov.uk](https://www.gov.uk/government/publications/companies-house-accreditation-to-information-fair-traders-scheme/public-task-copyright-and-crown-copyright)) | **Rights unclear** for republishing whole filings; extracted figures (facts) with citations are not affected |

## 2. What this means for the project

- **Published Jolpica-derived datasets** must state CC BY-NC-SA 4.0 and credit Jolpica-F1. The repository `LICENSE` already
  says datasets keep their sources' licences; the licence is now recorded in `config/sources.yaml`. The project is
  non-commercial, which the licence requires.
- **Model outputs and the paper** report the project's own analysis. They cite their sources; share-alike is applied
  conservatively to datasets that contain Jolpica-derived rows.
- **Hand-entered financial figures** (`financial_observations.csv`) are facts with page references; publishing them with
  citations is not affected by the filings' copyright.

## 3. Recommendations (need approval)

1. **FIA PDFs (9 files):** replace the hosted copies with a manifest of title, issue, URL, retrieval date and SHA-256 hash,
   so a reader can fetch the same document from the FIA and verify it. Article references in the paper stay as they are.
2. **Companies House filings (105 files):** either (a) keep them, with a notice that copyright belongs to the filing
   companies and that they are kept only so figures can be checked, and remove them on request; or (b) replace them with
   a manifest of company number, filing date, Companies House URL and SHA-256 hash, keeping `scripts/verify_large_changes.py`
   usable by downloading the filing first. Option (b) is the cautious choice; option (a) keeps the strongest provenance.
3. **Data explorer:** show each dataset's licence next to its download link.

Impact of removal on reproducibility: the models do not read the PDFs; only the OCR check of large changes and the
provenance explorer's "saved copy" links use them. A hash manifest keeps both verifiable.
