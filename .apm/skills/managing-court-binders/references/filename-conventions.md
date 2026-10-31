# BC Court Document Filename Conventions & Tab Ordering

This guide establishes the filename naming contract for ingesting raw folders of PDF documents into `bc-court-binder` when a `manifest.json` is not provided.

## Contents

- [Why Filename Conventions Matter](#why-filename-conventions-matter)
- [Statutory Chambers Tab Ordering](#statutory-chambers-tab-ordering)
- [Canonical Filename Schema](#canonical-filename-schema)
- [Exhibit & Sub-Bookmark Naming](#exhibit--sub-bookmark-naming)
- [Parsing Heuristic & Regex Contract](#parsing-heuristic--regex-contract)
- [Auto-Manifest Synthesis](#auto-manifest-synthesis)
- [Renaming Checklist for Paralegals & Agents](#renaming-checklist-for-paralegals--agents)

---

## Why Filename Conventions Matter

Under **Practice Direction 72 (PD-72)** and the **Court Services Online (CSO) April 2026 Guide**, court application records require:
1. **Strict Logical Tab Ordering:** Notice of Application must appear first (Tab 1), followed by responsive pleadings, supporting affidavits, draft orders, and authorities.
2. **Accurate Index Descriptions:** The 4-column Index table (`TAB`, `DOCUMENT`, `FILED DATE`, `PAGE`) must list clear, formal document descriptions rather than raw filenames (e.g., `Affidavit #1 of Eleanor Vance` instead of `scan_20261031_final.pdf`).
3. **Party Disambiguation:** Affidavits and responses must identify who made or filed them.

When building from an arbitrary folder of PDFs without an explicit `manifest.json`, the software parses the filenames to automatically infer Tab indices, document titles, and filing dates.

---

## Statutory Chambers Tab Ordering

In accordance with BC Supreme Court Civil Rule 8-1 and PD-72 §A.2, materials must be sequenced in this exact hierarchy:

| Tab | Statutory Document Category | Mandatory Form | Example |
| :---: | :--- | :--- | :--- |
| **Tab 1** | Notice of Application | Form 32 | `Tab01_Notice_of_Application_15Nov2026.pdf` |
| **Tab 2** | Application Response(s) | Form 33 | `Tab02_Application_Response_Defendant_18Nov2026.pdf` |
| **Tab 3+** | Affidavits in Support & Opposition | Form 35 | `Tab03_Affidavit_1_Eleanor_Vance_02Nov2026.pdf` |
| **Sub-Tabs** | Exhibits to Affidavits | Form 35 Annex | Nested under parent affidavit bookmark |
| **Next Tab** | Draft Order (if applicable) | Form 34 / 35 | `Tab04_Draft_Order_Discovery_20Nov2026.pdf` |
| **Next Tab** | Relevant Pleadings / Prior Orders | Forms 1, 2, 33 | `Tab05_Notice_of_Civil_Claim_10Oct2026.pdf` |
| **Final Tab**| Full-Text Legal Authorities | BCCA Rule 27 | `Tab06_Authority_Kalin_v_Campbell_2024_BCSC_123.pdf` |

---

## Canonical Filename Schema

All source PDF files within an input folder should conform to this naming format:

```text
Tab{NN}_{Document_Description}_{DDMmmYYYY}.pdf
```

### Components:
* **`Tab{NN}`**: Two-digit sequential Tab number (`Tab01`, `Tab02`, ... `Tab99`).
* **`{Document_Description}`**: Human-readable legal description with underscores or spaces:
  * Includes party disambiguation (e.g., `Affidavit_1_Eleanor_Vance`, `Response_Acme_Corp`).
* **`{DDMmmYYYY}`** *(Optional)*: Court filing date formatted as day, 3-letter month, and 4-digit year (e.g., `15Nov2026`, `02Dec2026`). If omitted, the Index table filed date defaults to `To be filed` or blank.

### Good vs. Bad Filename Examples:

| Status | Filename | Resulting Index Entry |
| :---: | :--- | :--- |
| ✔ **Good** | `Tab01_Notice_of_Application_15Nov2026.pdf` | Tab 1: Notice of Application (Filed: 15-Nov-2026) |
| ✔ **Good** | `Tab02_Application_Response_Acme_18Nov2026.pdf` | Tab 2: Application Response of Acme Corp (Filed: 18-Nov-2026) |
| ✔ **Good** | `Tab03_Affidavit_1_John_Doe_20Nov2026.pdf` | Tab 3: Affidavit #1 of John Doe (Filed: 20-Nov-2026) |
| ✖ **Bad** | `NOA.pdf` | Missing Tab number and formal description. |
| ✖ **Bad** | `scan00491.pdf` | Arbitrary scanner name; rejected by Rule 17. |
| ✖ **Bad** | `Affidavit_Final_v2_edit.pdf` | No Tab sequence; ambiguous version tag. |

---

## Exhibit & Sub-Bookmark Naming

When an affidavit contains separate PDF files for its exhibits, name them using this sub-tab schema:

```text
Tab{NN}_Ex{Letter}_{Exhibit_Description}.pdf
```

### Examples:
* `Tab03_ExA_Shareholders_Agreement_01Jan2024.pdf`
* `Tab03_ExB_Demand_Letter_14Aug2026.pdf`

This triggers the assembler to automatically nest Exhibit A and Exhibit B as child bookmarks under Tab 3 in the PDF Bookmarks panel (complying with **RULE-18**).

---

## Parsing Heuristic & Regex Contract

The automated pipeline parses filenames using this regular expression:

```python
import re

FILENAME_REGEX = re.compile(
    r"^(?:Tab_?|Item_?|)(\d{1,2})[-_.\s]+"      # Group 1: Tab Number
    r"(.+?)"                                      # Group 2: Document Description
    r"(?:[-_.\s]+(\d{1,2}[A-Za-z]{3}\d{4}))?"    # Group 3: Optional Date (DDMmmYYYY)
    r"\.pdf$",                                    # Extension
    re.IGNORECASE
)
```

### Extraction Mapping:
1. `Group 1` $\to$ `tab` integer (`1`, `2`, `3`).
2. `Group 2` $\to$ `title` string, replacing underscores with spaces and formatting legal titles (e.g. `Affidavit 1` $\to$ `Affidavit #1`).
3. `Group 3` $\to$ `filed_date` formatted string (e.g. `15-Nov-2026`).

---

## Auto-Manifest Synthesis

When `assembling_court_binders.py` runs on an input folder lacking `manifest.json`:
1. It lists all `.pdf` files and sorts them alphabetically by filename.
2. It parses each filename using `FILENAME_REGEX`.
3. If all files match the pattern, it automatically synthesizes an in-memory `manifest.json` and proceeds with two-pass assembly.
4. If non-conforming files are detected, it halts with a clear error listing the non-conforming filenames and linking to this document.

---

## Renaming Checklist for Paralegals & Agents

Before running `--mode assemble` on raw intake files:
1. [ ] Confirm Tab 1 is the Notice of Application (`Tab01_Notice_of_Application_...pdf`).
2. [ ] Check that each affidavit identifies the deponent and affidavit number (`Tab03_Affidavit_1_Jane_Smith_...pdf`).
3. [ ] Verify exhibits are either embedded in the affidavit or named with `ExA`, `ExB` sub-prefixes.
4. [ ] Ensure filing dates match the court registry stamp on the physical pleading.
5. [ ] Run `python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode validate` after assembly.
