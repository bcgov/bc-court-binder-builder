# BC Court Electronic Binder Builder

[![Compliance](https://img.shields.io/badge/BC%20Courts%20PD--72-20%2F20%20PASS-brightgreen)](#the-20-mandatory-court-quality-gates)
[![Jurisdiction](https://img.shields.io/badge/Jurisdiction-British%20Columbia%20(SC%20%26%20CA)-blue)](#key-technical-documentation)
[![Engine](https://img.shields.io/badge/Powered%20By-PdfCraft%20SDK-orange)](https://github.com/richfrem/pdfcraft)

An automated legal-ops pipeline for compiling, stamping, bookmarking, and validating **Electronic Application Records** and **Books of Authorities** for the Supreme Court of British Columbia and the Court of Appeal for British Columbia.

Strictly adheres to:
* **Practice Direction 72 (PD-72)**: Electronic Application Records
* **Practice Direction 73 (PD-73)**: Virtual Chambers & Microsoft Teams Hearings
* **Court Services Online (CSO)**: *Guide to Submitting Application Records* (April 2026 Edition)
* **BCCA Civil Rule 27**: Completion Instructions for Books of Authorities
* **Paralegal Best Practices**: Vancouver Senior Paralegal 9-Step Standard

---

## 🏛️ Strategic Purpose & Benefits
For a comprehensive breakdown of the institutional, operational, and economic drivers behind electronic chambers records, read:
👉 **[`COURT_PURPOSE_AND_BENEFITS.md`](COURT_PURPOSE_AND_BENEFITS.md)**
* **Judicial Mobility:** Allows remote judges across BC to access fully-indexed, searchable chambers binders instantly.
* **Provincial Workload Balancing:** Enables registries (e.g. Vancouver) to dynamically shift application records to available Associate Judges in other regions (Victoria, Kelowna, Prince George).
* **Registry Efficiencies:** Eliminates physical handling, shelving, boxing, and shredding of heavy 3-ring paper binders.
* **Litigant Cost Savings:** Saves litigants $1,000–$3,000 per application by eliminating paper printing, physical tabs, couriers, and attorney travel.
* **Hearing Docket Velocity:** Digital bookmark navigation and hyperlinked tables of contents accelerate chambers hearings.

---

## 📚 Key Technical Documentation

* **[`architecture.md`](architecture.md):** System architecture, legal taxonomy of submittable chambers matters (< 30 minutes before Associate Judges), and component layering.
* **[`BC_ELECTRONIC_BINDER_SPEC.md`](BC_ELECTRONIC_BINDER_SPEC.md):** Complete synthesis of the 9-step paralegal manual workflow (from Senior Vancouver Paralegal Video 836310097) vs. the automated SDK pipeline.
* **[`managing-court-binders/references/`](.apm/skills/managing-court-binders/references/):** Complete library of official court practice directions (`PD-72`, `PD-73`, `cso_application_record_guide_april2026.md`, source court PDFs, and all 13 BC Supreme Court PDF technical instruction guides).

---

## 🤖 Consolidated Agent Skill (`.apm/skills/managing-court-binders`)

This repository provides an APM-compliant, multi-mode domain skill for court binder operations:

| Skill | Path | Operational Modes |
| :--- | :--- | :--- |
| **`managing-court-binders`** | [`.apm/skills/managing-court-binders/`](.apm/skills/managing-court-binders) | • `generate`: Ingests or creates synthetic chambers filings<br/>• `assemble`: Compiles two-pass folios, index, and links<br/>• `validate`: Audits against 20 statutory quality gates<br/>• `all`: Full closed-loop execution |

---

## ⚖️ The 20 Mandatory Court Quality Gates

Every assembled binder is audited against 20 deterministic rules:

1. `RULE-00` (**Hard Stop**): Security & Encryption Disabled (no passwords).
2. `RULE-01` (**Hard Stop**): Single Consolidated PDF File (valid `%PDF-1.7` & `%%EOF`).
3. `RULE-02` (**Hard Stop**): CSO 50 MB File Size Ceiling Audit.
4. `RULE-03` (**Soft Warning**): Initial View Bookmarks Panel Default (`/PageMode /UseOutlines`).
5. `RULE-04` (**Hard Stop**): Form 22 / Form 30.001 Style of Cause Title Page (Item 1).
6. `RULE-05` (**Hard Stop**): Numbered Index / Table of Contents as Item 2.
7. `RULE-06` (**Hard Stop**): Exact Calculated Page Folios in Index.
8. `RULE-07` (**Soft Warning**): Hyperlinked Index Items (`/Subtype /Link`).
9. `RULE-08` (**Soft Warning**): Link Visual Appearance: Invisible Rectangle (`/Border [0 0 0]`), Highlight Style: None (`/H /N`).
10. `RULE-09` (**Soft Warning**): Universal GoTo Navigation Action (`/A << /S /GoTo /D [...] >>` & `/Dest`).
11. `RULE-10` (**Hard Stop**): Spatial Margin Top-Center Folio Placement ($x \approx 290\text{ pt}, y \approx 760\text{ pt}$).
12. `RULE-11` (**Soft Warning**): Folio Font Family (Standard-14 Arial/Helvetica).
13. `RULE-12` (**Soft Warning**): Folio Font Style (Bold).
14. `RULE-13` (**Soft Warning**): Folio Font Size ($14\text{--}16\text{ pt}$).
15. `RULE-14` (**Hard Stop**): Visible Page 1 Starts on Substantive Content (Notice of Application).
16. `RULE-15` (**Hard Stop**): Digital `/PageLabels` Synchronization with visual folios.
17. `RULE-16` (**Soft Warning**): Unnumbered Front Matter (`None` scheme for Title Page & Index).
18. `RULE-17` (**Hard Stop**): Meaningful Bookmarks with Party Disambiguation.
19. `RULE-18` (**Hard Stop**): Nested Exhibit Sub-Bookmarks, Searchable Vector/OCR Text ($H \ge 3.0$), and Full-Text Authorities Included.
20. `RULE-19` (**Soft Warning**): Standard North American Letter Page Geometry ($8.5 \times 11\text{ inches}$).

---

## 🚀 Quick Start

### 1. Python Pipeline (Fast, Zero Compiler Setup)
```bash
# Install dependencies
pip install -r requirements.txt

# Option A: Run the complete closed-loop lifecycle in one command
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode all

# Option B: Run individual steps as needed
# 1. Assemble an electronic court binder from input filings
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode assemble \
  --inputs inputs/01-commercial-discovery \
  --output output/01-commercial-discovery/Application_Record.pdf

# 2. Audit against the 20 BC Court compliance gates
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode validate \
  --output output/01-commercial-discovery/Application_Record.pdf
```

### 2. Rust Pipeline (Native `pdfcraft-sdk` Reference Engine)

The Rust runner in [`src/main.rs`](src/main.rs) is the native reference implementation that directly integrates with the in-process [`pdfcraft-sdk`](https://github.com/richfrem/pdfcraft) crate (`Layer 7`). It demonstrates how to build and verify a court application record without external CLI utilities.

#### What `cargo run` Does:
1. **In-Memory Legal Case Synthesis:** Instantiates a 5-document commercial discovery case (*Notice of Application*, *Application Response*, *Affidavit #1 of Eleanor Vance with Exhibits A & B*, *Draft Order*, and *Kalin v. Campbell* authority).
2. **Dynamic Folio & Index Math:** Calculates exact folio target coordinates starting at **Page 1 on Tab 1** (leaving Title & Index unnumbered per Rule 16).
3. **Vector PDF Generation:** Generates the Title page and 4-column Index table (`TAB`, `DOCUMENT`, `FILED DATE`, `PAGE`) with invisible rectangle GoTo hyperlinks (`/Border [0 0 0]`, `/H /N`).
4. **Folio Stamping & Digital Metadata:** Injects $15\text{ pt}$ Bold Helvetica top-center page folios, sets `/PageLabels`, and configures Initial View (`/PageMode /UseOutlines`).
5. **PdfCraft SDK Verification:** Calls `pdfcraft_sdk::LocalClient::default().render_page(&src, 1, ...)` to mathematically verify that the PdfCraft rasterization engine renders Page 1 without syntax errors.
6. **CSO Audit & File Output:** Audits the generated PDF against the $50\text{ MB}$ Court Services Online limit and writes the file.

```bash
# Prerequisites: Rust 1.80+ (https://rustup.rs or `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
# Execute the native Rust pipeline
cargo run
```

#### Output Artifact:
```text
output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf
```

#### Sample Terminal Output:
```text
================================================================================
   BRITISH COLUMBIA ELECTRONIC APPLICATION RECORD BUILDER (PD-72 & CSO POC)     
   Synthesized from BC Court Rules, CSO User Guides & Senior Paralegal Practice 
================================================================================

Step 1: Ingesting source documents and exhibit metadata...
Step 2: Calculating dynamic page numbering, folios, and bookmarks...
   -> Front matter: 2 pages (Title page + dynamic Index)
   -> Tab 1 starts at visible Page 1 (foliated continuous)
   -> Total substantive content: 15 pages across 5 items
   -> Total application record size: 17 pages
Step 3: Generating PDF byte stream with vector layout...
Step 4: Compiling hierarchical bookmark outline tree and link annotations...
Step 5: Verifying PDF with PdfCraft LocalClient...
   -> PdfCraft engine raster verification passed: Page 1 rendered successfully
Step 6: Executing CSO pre-flight compliance audit...

SUCCESS: Compliant Electronic Application Record generated!
  File Path: output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf
  File Size: 18.42 KB (0.0176 MB)
  CSO Audit: PASS (Within strict 50 MB Court Services Online ceiling)

=== Professional Paralegal Workflow Checklist (Video 836310097) ===
✔ [Step 1] Source PDFs ingested with logical sequence order.
✔ [Step 2] Content compiled into single continuous PDF stream.
✔ [Step 3] Bookmarks panel populated with clear titles and exhibit sub-bookmarks.
✔ [Step 4] Top-center 14-16pt bold page numbers stamped across content pages.
✔ [Step 5] Title page & dynamic Index generated with accurate calculated folios.
✔ [Step 6] Text searchability verified (ready for OCR layer).
✔ [Step 7] Visual folios align precisely with index numbers.
✔ [Step 8] Hyperlink structure verified from Index entries to targets.
✔ [Step 9] File size audited and verified under 50 MB threshold.
```

---

### 💡 Which Pipeline Should I Use?

| Feature | Python Pipeline (`.apm/skills/`) | Rust Pipeline (`cargo run`) |
| :--- | :--- | :--- |
| **Primary Use Case** | Day-to-day legal operations, batch processing, and AI Agent execution | Core engine development and SDK integration testing |
| **Input Source** | Dynamic JSON manifests & arbitrary PDFs (`inputs/<scenario>/`) | Hardcoded commercial discovery test case in `src/main.rs` |
| **Startup Time** | Instant (< 1 second) | Requires initial `cargo build` compilation |
| **Disk Requirement** | Lightweight (< 1 MB cache) | Generates compiler cache in `target/` (~1 GB) |
| **Customizability** | Drop any PDF or exhibit into `inputs/` | Edit Rust structs in `src/main.rs` |

---

## 📄 License
Dual-licensed under MIT or Apache-2.0.
