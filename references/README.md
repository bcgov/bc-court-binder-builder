# Reference Documents & Court Specifications

This folder contains the complete, authoritative reference library for British Columbia electronic court filings and PDF application record requirements.

All reference materials are consolidated into **3 core Markdown reference documents**, with the original source PDF files stored in a single flat [`pdfs/`](pdfs/) directory.

---

## 📚 1. Core Reference Documents

| Document | Focus & Scope | Key Statutory Authorities |
| :--- | :--- | :--- |
| **[`court_practice_directions.md`](court_practice_directions.md)** | Consolidates all official court practice directions and electronic filing rules. | **PD-72** (Electronic Application Records), **PD-73** (Virtual Chambers), **CSO Guide** (< 50 MB limits, workflow), **BCCA Rule 27** (Books of Authorities), and the 2026 Associate Judges Sitting Schedule. |
| **[`pdf_instructions.md`](pdf_instructions.md)** | Complete 13-Part Supreme Court PDF Technical Instruction Manual. | Guides 01–13 (single-volume merging, Index/TOC formatting, bookmarks tree, `/PageMode /UseOutlines` initial view, invisible rectangle hyperlinks, top-center 14–16pt bold Arial folios, `/PageLabels` alignment, and OCR). |
| **[`paralegal_video_workflow.md`](paralegal_video_workflow.md)** | Real-world litigation practice analysis & timestamped transcript. | 20-Year Vancouver Senior Litigation Paralegal video demonstration (Vimeo 836310097) mapping the 9-step manual Acrobat process (45–90 min) to the automated SDK pipeline (< 200 ms). |

---

## 📁 2. Directory Layout

```
poc/court-binder/references/
├── README.md                      # This reference index and overview
├── court_practice_directions.md    # Consolidated statutory rules (PD-72, PD-73, CSO, BCCA)
├── pdf_instructions.md            # Consolidated 13-part BC Supreme Court PDF manual
├── paralegal_video_workflow.md    # Paralegal video analysis & timestamped transcript
├── pdfs/                          # Single flat archive of all 18 source court PDFs (gitignored)
│   ├── PD-72_Electronic_Application_Records.pdf
│   ├── PD-73_Virtual_Chambers.pdf
│   ├── InstructionsForUsersForApplicationRecords.pdf
│   ├── e_completion_instructions_book_of_authorities.pdf
│   ├── ASSOCIATE_JUDGES_VIRTUAL_CHAMBERS_SITTING_SCHEDULE_2026.pdf
│   └── [13 Supreme Court Instruction Guide PDFs...]
└── video-screenshots/             # Screenshot frames documenting the 9 Acrobat steps (gitignored)
```

---

## ⚖️ 3. Quick Reference: Core Filing Rules

1. **Document Ordering:** Form 22 Title Page (Item 1) &rarr; Numbered Index (Item 2) &rarr; Substantive Filings (NOA, Response, Affidavits with Exhibits, Draft Order, Authorities).
2. **Page Numbering:** Top-center of each substantive page, formatted in **14–16 pt Bold Arial/Helvetica**.
3. **Digital Page Labels:** Synchronized via `/PageLabels` (Front matter = `None`, Substantive tabs = `1..N`).
4. **Interactive Navigation:** Index entries link to target pages using invisible rectangles (`/Border [0 0 0] /H /N`). Initial view opens with bookmarks expanded (`/PageMode /UseOutlines`).
5. **CSO Size Threshold:** Strict **50 MB** ceiling per electronic filing volume.
