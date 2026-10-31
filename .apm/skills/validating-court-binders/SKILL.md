---
name: validating-court-binders
description: "Validates electronic PDF binders against BC Supreme Court PD-72, Court Services Online (CSO), and Court of Appeal Rule 27 completion rules. Use when auditing court binders for bookmarks, initial view settings, index hyperlinks, top-center page numbers, or CSO 50 MB limits."
argument-hint: "[--file <pdf_path>] [--json]"
allowed-tools: Bash, Read
---

# Validating Court Binders

Audits an assembled electronic court binder PDF against British Columbia legal filing standards (BC Supreme Court PD-72 Appendix A, Virtual Chambers PD-73, CSO 50 MB limits, and Court of Appeal Civil Rule 27), incorporating Ministry of Attorney General (`JAG-CSO-Assistant`) enterprise validation architecture.

Evaluates the complete **20-Gate Quality & Compliance Matrix** featuring 3-tier severity classification:
* `HARD_STOP`: Fatal court registry rejection (encryption, oversized file, missing title page, missing index, missing page 1 start, desynced `/PageLabels`, truncated content).
* `SOFT_WARNING`: Format & accessibility advisories (link appearance, initial view outlines, font size, non-standard letter geometry, OCR noise).
* `PASS`: Fully compliant gate.

## Contents

- [The 20 Evaluated Court Quality Gates](#the-20-evaluated-court-quality-gates)
- [Enterprise Features from JAG-CSO-Assistant](#enterprise-features-from-jag-cso-assistant)
- [Quick Start](#quick-start)
- [JSON Automation Receipt](#json-automation-receipt)
- [Authoritative References](#authoritative-references)
- [Remediation Playbook](#remediation-playbook)

---

## The 20 Evaluated Court Quality Gates

| Rule ID | Severity | Quality Gate Description | Statutory Authority Reference | Passing Criteria |
| :--- | :---: | :--- | :--- | :--- |
| `RULE-00` | `HARD_STOP` | **Security & Encryption Disabled** | CSO Guide §2; JAG PD72-R5 | Document is unencrypted and opens without passwords or permissions blocks. |
| `RULE-01` | `HARD_STOP` | **Single Consolidated PDF File** | `PD-72` §A.1; CSO Guide §2; Video `00:22` | PDF container begins with `%PDF-` and ends with valid `%%EOF` marker. |
| `RULE-02` | `HARD_STOP` | **CSO File Size Governance (< 50 MB)** | CSO Instructions §3; Video `07:47` | File size is strictly <= 50.0 MB (52,428,800 bytes). |
| `RULE-03` | `SOFT_WARNING` | **Initial View Bookmarks Panel Default** | `PD-72` §A.3; Court PDF Guide 12 | Catalog dictionary contains `/PageMode /UseOutlines` to expand outlines automatically. |
| `RULE-04` | `HARD_STOP` | **Form 22 Style of Cause (Title Page)** | `PD-72` §A.2; Video `00:22` | Item 1 contains court header, registry, file number, style of cause, and counsel. |
| `RULE-05` | `HARD_STOP` | **Index / Table of Contents Position** | `PD-72` §A.2; Court PDF Guide 02 | Numbered Index is positioned directly behind Title Page and ahead of substantive tabs. |
| `RULE-06` | `HARD_STOP` | **Page Number Entry in Index** | `PD-72` §A.2; Video `05:44` | Every listed filing and authority carries exact calculated folio page numbers. |
| `RULE-07` | `SOFT_WARNING` | **Hyperlinked Index Items** | `PD-72` §A.2; Court PDF Guide 06 | Contains active `/Subtype /Link` annotations spanning Index entries. |
| `RULE-08` | `SOFT_WARNING` | **Link Visual Appearance (Invisible / None)** | Court PDF Guide 06; Video `06:14` | Link annotations set to `/Border [0 0 0]` (Invisible) and `/H /N` (Highlight Style: None). |
| `RULE-09` | `SOFT_WARNING` | **Bookmark Tab Navigation Integration** | Court PDF Guide 06; Video `06:40` | Link targets route directly to designated page view coordinates (`/Dest [obj R /Fit]` or `/GoTo`). |
| `RULE-10` | `HARD_STOP` | **Spatial Margin Top-Center Folio Placement** | Court PDF Guide 09; Video `02:40`; JAG PD72-R7 | Bounding box coordinates confirm folio is in top 100 pt and centered ($0.35 \le x/w \le 0.65$). |
| `RULE-11` | `SOFT_WARNING` | **Page Number Font Family** | Court PDF Guide 09; Video `02:22` | Header stamping uses standard Arial/Helvetica standard-14 type family. |
| `RULE-12` | `SOFT_WARNING` | **Page Number Font Style** | Court PDF Guide 09; Video `02:25` | Page number font is styled in Bold (`/BaseFont /Helvetica-Bold`). |
| `RULE-13` | `SOFT_WARNING` | **Page Number Font Size** | Court PDF Guide 09; Video `02:30` | Folio font size set within 14 pt – 16 pt range (`15 Tf`). |
| `RULE-14` | `HARD_STOP` | **Page 1 Start Location on Substantive Content** | Court PDF Guide 10; Video `04:17` | Visible sequential numbering starts at `1` on Tab 1 (Notice of Application). |
| `RULE-15` | `HARD_STOP` | **Page Labeling Synchronization (`/PageLabels`)** | Court PDF Guide 10; Video `04:17` | Catalog contains `/PageLabels` dictionary aligning PDF reader counter with visual folios. |
| `RULE-16` | `SOFT_WARNING` | **Unnumbered Front Matter Labels** | Court PDF Guide 10; Video `04:45` | Title Page & Index configured with `/S /None` label scheme. |
| `RULE-17` | `HARD_STOP` | **Descriptive Bookmark Titles & Disambiguation** | `PD-72` §A.3; Court PDF Guides 03 & 04 | Outline items name specific documents and disambiguate parties (e.g. *Jane Doe*). |
| `RULE-18` | `HARD_STOP` | **Exhibit Sub-Bookmarks, OCR & Content Integrity** | `PD-72` §A.3, §A.4; JAG PD72-R1/R8 | Affidavits feature nested exhibit bookmarks; no pages truncated/blank; passes Shannon entropy OCR test. |
| `RULE-19` | `SOFT_WARNING` | **Page Geometry & Standard Dimensions** | JAG PD72-R4; Arlington Model §7.7 | $\ge 90\%$ of pages conform to standard 8.5 x 11 inch Letter boundaries ($612 \times 792$ pt). |

---

## Enterprise Features from JAG-CSO-Assistant

1. **Spatial Bounding Box Margin Analysis**: Evaluates text block centroids $\frac{x_0 + x_1}{2}$ to mathematically verify that folios are centered in the top header margin rather than placed in footers or side margins.
2. **Deterministic Shannon Character Entropy & Dictionary Quality**: Analyzes character distribution entropy ($H = -\sum p \log_2 p$) and legal dictionary hit ratio to flag corrupted, unreadable, or garbled OCR scans.
3. **Substantive Content Completeness**: Evaluates word and line counts across all substantive pages to detect empty, blank, or partially truncated document generation.
4. **Page Geometry Auditing**: Scans `MediaBox` bounds to ensure documents adhere to standard North American Letter format without oversized landscape anomalies.

---

## Quick Start

Validate an electronic court binder and display the categorized scorecard:

```bash
python3 poc/court-binder/.apm/skills/validating-court-binders/scripts/validating_court_binders.py \
  --file poc/court-binder/output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf
```

Exit code:
* `0`: Fully Compliant (0 Hard Stops) — Approved for CSO submission.
* `1`: Non-Compliant — Hard stop violations present; document will be rejected by registry.

---

## JSON Automation Receipt

Generate structured JSON output for automated CI pipelines or agent tool execution:

```bash
python3 poc/court-binder/.apm/skills/validating-court-binders/scripts/validating_court_binders.py \
  --file poc/court-binder/output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf \
  --json
```

---

## Authoritative References

* **CSO Application Records Guide (April 2026)**: [`references/cso_application_record_guide_april2026.md`](references/cso_application_record_guide_april2026.md)
* **Consolidated Court Rules & Directives (PD-72, PD-73)**: [`references/court_practice_directions.md`](references/court_practice_directions.md)
* **BC Supreme Court PDF Technical Manual (Guides 01–13)**: [`references/pdf_instructions.md`](references/pdf_instructions.md)
* **Paralegal Video Workflow & Standards**: [`references/paralegal_video_workflow.md`](references/paralegal_video_workflow.md)
* **Source PDF Archive**: [`../../../references/pdfs/`](../../../references/pdfs/)

---

## Remediation Playbook

If a binder fails validation, apply these standard fixes:
* **`RULE-00` Failed**: Remove password protection and user permissions using `qpdf --decrypt` or Adobe Acrobat security settings.
* **`RULE-03` Failed**: In catalog dictionary, add `/PageMode /UseOutlines`.
* **`RULE-08` Failed**: Update link annotations to include `/Border [0 0 0]` and `/H /N`.
* **`RULE-10` Failed**: Adjust Header & Footer positioning to stamp folios at top-center ($x \approx 290\text{ pt}, y \approx 760\text{ pt}$).
* **`RULE-15`–`RULE-16` Failed**: Ensure catalog defines `/PageLabels << /Nums [0 << /S /None >> 2 << /S /D /St 1 >>] >>`.
* **`RULE-18` Failed**: 
  - If truncated/empty pages: Fix PDF generation line advances (`TL` leading and `T*` line drops).
  - If garbled OCR: Re-scan document at 300+ DPI and re-run OCR engine.
  - If flat bookmarks: Nest exhibit bookmarks under parent affidavit bookmarks.
* **`RULE-19` Failed**: Scale or re-print non-standard pages to 8.5 × 11 inches.
