# Assembling Court Binders

Assembles raw court filing PDFs and manifests into an electronic court application record or book of authorities strictly adhering to British Columbia court quality gates, synthesized from:
* [BC Supreme Court Practice Direction 72 (PD-72)](court_practice_directions.md)
* [BC Supreme Court Practice Direction 73 (PD-73)](court_practice_directions.md)
* [Court Services Online (CSO) User Guide](cso_application_record_guide_april2026.md)
* [BC Court of Appeal Civil Rule 27 Completion Instructions](court_practice_directions.md)
* [BC Supreme Court 13-Part PDF Technical Instructions Library](pdf_instructions.md)
* [Professional Paralegal 9-Step Synthesis Workflow](paralegal_video_workflow.md)

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
4. **Link Visual Appearance**: Link annotations over index lines must be set to `Invisible Rectangle` (`/Border [0 0 0]`) with Highlight Style set to `None` (`/H /N`) (Court Guide 06).
5. **Bookmark Tab Integration**: Link actions must navigate directly to the target page view destination (`/Dest [obj R /Fit]` or `/S /GoTo`) aligned with the bookmark tree.
6. **Top-Center Folio Placement**: Page numbers must appear in the top-center margin of every substantive page (`x ~ 290 pt, y ~ 760 pt` on letter size) (Court Guide 09).
7. **Page Number Font Family**: Stamped folios must use Arial (or Helvetica standard-14 metric alias) (Court Guide 09).
8. **Page Number Font Style**: Stamped folios must be styled in Arial/Helvetica Bold (`/BaseFont /Helvetica-Bold`) (Court Guide 09).
9. **Page Number Font Size**: Stamped folios must be set to 14 pt or 16 pt font size (`15 Tf`) to remain visibly distinct from body text (Court Guide 09).
10. **Page 1 Start Location**: Sequential visible page numbering begins at `1` on the first substantive document (Notice of Application). Title Page and Index do not carry printed folios.
11. **Digital Page Labels (`/PageLabels`)**: Catalog `/PageLabels` dictionary must be synchronized with printed folios so entering a number in the PDF viewer navigates to the matching printed page (Court Guide 10).
12. **Unnumbered Front Matter Labels**: Front matter (Title Page and Index) page label style must be set to `None` (`/Nums [0 << /S /None >> 2 << /S /D /St 1 >>]`) (Court Guide 10).
13. **Descriptive Bookmark Titles**: Every document merged into the record must have a clearly descriptive bookmark identifying the specific filing (`PD-72` §A.3; Court Guide 03).
14. **Disambiguation of Similar Titles**: If multiple documents share similar titles, bookmarks must distinguish them by party name (e.g. *Application Response of Jane Doe*, *Application Response of Peter Smith*) (`PD-72` §A.3).
15. **Affidavit Exhibit Sub-Bookmarks**: All exhibits attached to affidavits must be nested as sub-bookmarks under the parent affidavit bookmark, formatted with the exhibit letter and description (e.g. *Exhibit A - Joint Venture Agreement*) (Court Guide 04).
16. **Full-Text Searchability (OCR/Vector)**: All text across the document must be fully selectable and searchable via digital vector text streams or OCR text layers (`PD-72` §A.4; Court Guide 11).
17. **File Size Limit (< 50 MB)**: The assembled PDF must remain strictly under 50 MB (52,428,800 bytes) for Court Services Online (CSO) submission acceptance (CSO Instructions §3).
18. **Single Consolidated PDF File**: The entire application record (cover, index, pleadings, affidavits, exhibits, authorities) must be submitted as a single consolidated PDF volume (`PD-72` §A.1; CSO Guide §2).

---

## Quick Start

Assemble an electronic court application record:

```bash
python3 .apm/skills/managing-court-binders/scripts/assembling_court_binders.py \
  --inputs inputs/01-commercial-discovery \
  --output output/01-commercial-discovery/Application_Record.pdf
```

---

## Workflow Architecture

```text
[Inputs: Manifest + Component Filings]
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

## True Copies, Bookmarks and the Index

CSO requires every document in an application record to be a **true copy** of the original. The assembler therefore:

- **Uses each filing's original PDF pages.** A filing that is a readable PDF goes into the binder with its content, page size, rotation and annotations untouched. Only the cover page, the index and the folio numbers are added. A filing that exists only as text (no PDF) is typeset from the text and the assembler prints a `WARNING` that it is not a true copy. `--retypeset` forces typesetting for every filing (not recommended for filing).
- **Stamps the folio on top of the original page**: Helvetica-Bold 15 pt, top centre, upright even on pages rotated 90, 180 or 270 degrees.
- **Builds the bookmark tree.** The cover, the index and each filing are top-level bookmarks. A filing's exhibits are child bookmarks under it, found from the manifest or from their "This is Exhibit ... referred to" stamps, including an exhibit that starts on the filing's first page.
- **Spills a long index onto more pages.** Roughly 24 rows fit on a page; further pages are headed "(continued)", every link points at the right page, and `/PageLabels` leaves all the cover and index pages unnumbered. The validator reads the number of front-matter pages from the page labels.
- **Keeps scans as they are.** A filing with no text (a scan) is included unchanged and gate 18 flags it: run OCR on it first. Text typeset by the assembler uses Western European characters only; anything else is reported.

How it works: the assembler writes the cover, index, bookmarks, links and page labels around blank placeholder pages, then copies each original page into its placeholder. Nothing that points at a page (links, bookmarks) has to change.

**Orientation.** Pages may be portrait, landscape or rotated. The folio is placed, and the validator looks for it, at the top centre of the page *as displayed* (after `/Rotate`), so no orientation is assumed. None of the court guides in this repository states an orientation rule; gate 19 accepts Letter size in either orientation (612 x 792 or 792 x 612 pt, within 15 pt) and warns on other sizes.

Known limit: links inside original PDFs (including web links in authorities) are kept as they are.

## Case Details and manifest.json

The title page prints the court, registry, court file number, both parties and hearing date, plus the time estimate and counsel for each side when provided (those three are optional and left off the page when blank; nothing is invented). These come from `manifest.json` in the input folder, which the assembler cannot guess from filenames. Without it the title page carries clearly marked placeholders and exhibits are not bookmarked, and the assembler prints a warning.

Provide them with the command-line options (they write or update `manifest.json`, keeping any documents and exhibits already in it):

```bash
python3 scripts/managing_court_binders.py --mode assemble --inputs inputs/my-matter \
  --output output/my-matter/Application_Record_my-matter_15Nov2026.pdf \
  --registry Vancouver --file-number "S-123456" --plaintiff "Roe Holdings Ltd." \
  --defendant "Doe Corp." --hearing-date "November 15, 2026"
```

Agents must ask the user for these values and must never reuse sample values. The desktop app collects the same fields in a "Case details" form and calls the same functions (`read_case_details`, `save_case_details`, `suggest_binder_name` in `assembling_court_binders.py`).

## Authoritative References

* **CSO Application Records Guide (April 2026)**: [`cso_application_record_guide_april2026.md`](cso_application_record_guide_april2026.md)
* **Consolidated Court Rules & Directives (PD-72, PD-73)**: [`court_practice_directions.md`](court_practice_directions.md)
* **BC Supreme Court PDF Technical Manual (Guides 01–13)**: [`pdf_instructions.md`](pdf_instructions.md)
* **Paralegal Video Workflow & Standards**: [`paralegal_video_workflow.md`](paralegal_video_workflow.md)

---

## Verification

Verify output existence and validate with the validator script:

```bash
ls -lh output/01-commercial-discovery/Application_Record.pdf
python3 .apm/skills/managing-court-binders/scripts/validating_court_binders.py \
  --file output/01-commercial-discovery/Application_Record.pdf
```
