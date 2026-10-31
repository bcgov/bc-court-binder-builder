---
name: assembling-court-binders
description: "Assembles input court documents into a fully compliant BC Supreme Court PD-72 Electronic Application Record or Court of Appeal Book of Authorities. Use when compiling electronic court binders, generating two-pass indexes, stamping folios, setting bookmarks, or applying CSO 50 MB governance."
argument-hint: "[--inputs <dir>] [--output <file>]"
allowed-tools: Bash, Read, Write
---

# Assembling Court Binders

Assembles raw court filing PDFs and manifests into an electronic court application record or book of authorities strictly adhering to the 18 British Columbia court quality gates, synthesized from:
* [BC Supreme Court Practice Direction 72 (PD-72)](../../../references/court_practice_directions.md#1-practice-direction-72-pd-72--electronic-application-records)
* [BC Supreme Court Practice Direction 73 (PD-73)](../../../references/court_practice_directions.md#2-practice-direction-73-pd-73--virtual-chambers)
* [Court Services Online (CSO) User Guide](../../../references/court_practice_directions.md#3-cso-guide-to-submitting-application-records)
* [BC Court of Appeal Civil Rule 27 Completion Instructions](../../../references/court_practice_directions.md#4-bcca-civil-rule-27-completion-instructions-books-of-authorities)
* [BC Supreme Court 13-Part PDF Technical Instructions Library](../../../references/pdf_instructions.md)
* [Professional Paralegal 9-Step Synthesis Workflow](../../../references/paralegal_video_workflow.md)

## Contents

- [The 18 Mandatory Court Specifications](#the-18-mandatory-court-specifications)
- [Quick Start](#quick-start)
- [Workflow Architecture](#workflow-architecture)
- [Authoritative References](#authoritative-references)
- [Verification](#verification)

---

## The 18 Mandatory Court Specifications

Every assembled binder must strictly adhere to these 18 rules:

1. **Document Ordering**: Form 22 Cover Page is always Item 1; Numbered Index is always Item 2; followed by Pleadings, Affidavits with Exhibits, Draft Order, and Legal Authorities (`PD-72` §A.1–A.2).
2. **Calculated Page Folios in Index**: Index page numbers must precisely match the visual stamped folio of every document and authority.
3. **Hyperlinked Index Items**: Every listed item in the Index must feature an active link annotation jumping directly to its destination page (`PD-72` §A.2; Court Guide 06).
4. **Link Visual Appearance**: Link annotations over index lines must be set to `Invisible Rectangle` (`/Border [0 0 0]`) with Highlight Style set to `None` (`/H /N`) (Court Guide 06; Video `06:14`).
5. **Bookmark Tab Integration**: Link actions must navigate directly to the target page view destination (`/Dest [obj R /Fit]` or `/S /GoTo`) aligned with the bookmark tree.
6. **Top-Center Folio Placement**: Page numbers must appear in the top-center margin of every substantive page (`x ~ 290 pt, y ~ 760 pt` on letter size) (Court Guide 09; Video `02:40`).
7. **Page Number Font Family**: Stamped folios must use Arial (or Helvetica standard-14 metric alias) (Court Guide 09; Video `02:22`).
8. **Page Number Font Style**: Stamped folios must be styled in Arial/Helvetica Bold (`/BaseFont /Helvetica-Bold`) (Court Guide 09; Video `02:25`).
9. **Page Number Font Size**: Stamped folios must be set to 14 pt or 16 pt font size (`15 Tf`) to remain visibly distinct from body text (Court Guide 09; Video `02:30`).
10. **Page 1 Start Location**: Sequential visible page numbering begins at `1` on the first substantive document (Notice of Application). Title Page and Index do not carry printed folios.
11. **Digital Page Labels (`/PageLabels`)**: Catalog `/PageLabels` dictionary must be synchronized with printed folios so entering a number in the PDF viewer navigates to the matching printed page (Court Guide 10; Video `04:17`).
12. **Unnumbered Front Matter Labels**: Front matter (Title Page and Index) page label style must be set to `None` (`/Nums [0 << /S /None >> 2 << /S /D /St 1 >>]`) (Court Guide 10; Video `04:45`).
13. **Descriptive Bookmark Titles**: Every document merged into the record must have a clearly descriptive bookmark identifying the specific filing (`PD-72` §A.3; Court Guide 03).
14. **Disambiguation of Similar Titles**: If multiple documents share similar titles, bookmarks must distinguish them by party name (e.g. *Application Response of Jane Doe*, *Application Response of Peter Smith*) (`PD-72` §A.3; Video `01:10`).
15. **Affidavit Exhibit Sub-Bookmarks**: All exhibits attached to affidavits must be nested as sub-bookmarks under the parent affidavit bookmark, formatted with the exhibit letter and description (e.g. *Exhibit A - Joint Venture Agreement*) (Court Guide 04; Video `01:40`).
16. **Full-Text Searchability (OCR/Vector)**: All text across the document must be fully selectable and searchable via digital vector text streams or OCR text layers (`PD-72` §A.4; Court Guide 11).
17. **File Size Limit (< 50 MB)**: The assembled PDF must remain strictly under 50 MB (52,428,800 bytes) for Court Services Online (CSO) submission acceptance (CSO Instructions §3; Video `07:47`).
18. **Single Consolidated PDF File**: The entire application record (cover, index, pleadings, affidavits, exhibits, authorities) must be submitted as a single consolidated PDF volume (`PD-72` §A.1; CSO Guide §2).

---

## Quick Start

Assemble an electronic court application record:

```bash
python3 poc/court-binder/.apm/skills/assembling-court-binders/scripts/assembling_court_binders.py \
  --inputs poc/court-binder/inputs/01-commercial-discovery \
  --output poc/court-binder/output/01-commercial-discovery/Application_Record.pdf
```

---

## Workflow Architecture

```
[Inputs: Manifest + Component PDFs]
                 │
                 ▼
 ┌────────────────────────────────────────────────────────┐
 │ Pass 1: Probing & Folio Calculation                    │
 │ - Read component page counts                           │
 │ - Calculate exact folios for all tabs & authorities    │
 │ - Determine total volume size                          │
 └────────────────────────────────────────────────────────┘
                 │
                 ▼
 ┌────────────────────────────────────────────────────────┐
 │ Pass 2: Document Generation & Stamping                 │
 │ - Synthesize Form 22 Title Page (Item 1)               │
 │ - Generate Numbered Index (Item 2) with folios         │
 │ - Stamp Top-Center 15pt Bold folios on content pages   │
 │ - Assemble single continuous PDF stream                │
 └────────────────────────────────────────────────────────┘
                 │
                 ▼
 ┌────────────────────────────────────────────────────────┐
 │ Pass 3: Metadata, Navigation & Security                │
 │ - Inject Initial View (/PageMode /UseOutlines)         │
 │ - Build hierarchical Outlines (Affidavits + Exhibits)  │
 │ - Inject Invisible Rectangle links (/Border [0 0 0])   │
 │ - Set Highlight None (/H /N)                           │
 │ - Synchronize digital /PageLabels (None, 1..N)         │
 │ - Enforce CSO < 50 MB compression                      │
 └────────────────────────────────────────────────────────┘
                 │
                 ▼
[Output: 100% Compliant Application Record PDF]
```

---

## Authoritative References

* **CSO Application Records Guide (April 2026)**: [`references/cso_application_record_guide_april2026.md`](references/cso_application_record_guide_april2026.md)
* **Consolidated Court Rules & Directives (PD-72, PD-73)**: [`references/court_practice_directions.md`](references/court_practice_directions.md)
* **BC Supreme Court PDF Technical Manual (Guides 01–13)**: [`references/pdf_instructions.md`](references/pdf_instructions.md)
* **Paralegal Video Workflow & Standards**: [`references/paralegal_video_workflow.md`](references/paralegal_video_workflow.md)
* **Source PDF Archive**: [`../../../references/pdfs/`](../../../references/pdfs/)

---

## Verification

Audit the newly assembled binder with `validating-court-binders`:

```bash
python3 poc/court-binder/.apm/skills/validating-court-binders/scripts/validating_court_binders.py \
  --file poc/court-binder/output/01-commercial-discovery/Application_Record.pdf
```
