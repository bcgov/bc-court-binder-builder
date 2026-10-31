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
* **[`references/`](references/):** Complete library of official court practice directions (`PD-72`, `PD-73`, `cso_application_record_guide_april2026.md`, and all 13 BC Supreme Court PDF technical instruction guides).

---

## 🤖 Modular Agent Skills (`.apm/skills/`)

This repository includes self-contained APM agent skills for building and auditing court binders:

| Skill | Path | Description |
| :--- | :--- | :--- |
| **`assembling-court-binders`** | [`.apm/skills/assembling-court-binders/`](.apm/skills/assembling-court-binders) | Executes the automated 9-step compilation, two-pass folios, bookmarks, and hyperlinked Index table. |
| **`validating-court-binders`** | [`.apm/skills/validating-court-binders/`](.apm/skills/validating-court-binders) | Audits any PDF binder against the complete 20 BC Court quality gates (exits 0 on 100% compliance). |

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

# 1. Assemble an electronic court binder from input filings
python3 .apm/skills/assembling-court-binders/scripts/assembling_court_binders.py \
  --inputs inputs/01-commercial-discovery \
  --output output/01-commercial-discovery/Application_Record.pdf

# 2. Audit against the 20 BC Court compliance gates
python3 .apm/skills/validating-court-binders/scripts/validating_court_binders.py \
  --file output/01-commercial-discovery/Application_Record.pdf
```

### 2. Rust Pipeline
```bash
cargo run
```

---

## 📄 License
Dual-licensed under MIT or Apache-2.0.
