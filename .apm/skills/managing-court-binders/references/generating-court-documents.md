# Generating Court Documents

Generates standardized, synthetic British Columbia court filing PDFs (Form 32 Notice of Application, Form 33 Response, Affidavit with Exhibit A & B, Form 35 Draft Order, and Legal Authorities) plus an ingestion `manifest.json`.

## Contents

- [Constraints](#constraints)
- [Quick Start](#quick-start)
- [Generated Filings](#generated-filings)
- [Prompt Library](#prompt-library)
- [Workflow](#workflow)
- [Verification](#verification)

---

## Constraints

1. **Deterministic Streams**: Generates valid PDF 1.7 streams without third-party external library dependencies.
2. **Metadata Contract**: Every batch emits an accompanying `manifest.json` describing document sequence, titles, and exhibit hierarchy.
3. **Court Form Alignment**: Headers and content align with BC Supreme Court Civil Rules (Forms 32, 33, 35) and PD-72.

---

## Quick Start

Generate synthetic court input files into `inputs/01-commercial-discovery`:

```bash
python3 .apm/skills/managing-court-binders/scripts/generating_court_documents.py \
  --output-dir inputs/01-commercial-discovery \
  --matter-type discovery
```

---

## Generated Filings

| Document | Court Form / Rule | Exhibits / Structure |
| :--- | :--- | :--- |
| `01_Notice_of_Application.txt` | Form 32 (Civil Rule 8-1(4)) | Order sought, factual basis, legal grounds |
| `02_Application_Response.txt` | Form 33 (Civil Rule 8-1(9)) | Response to orders, consent/opposed terms |
| `03_Affidavit_1_Eleanor_Vance.txt` | Affidavit (Civil Rule 22-2) | Includes Exhibit A (Contract) & Exhibit B (Notice) |
| `04_Draft_Order.txt` | Form 35 (Civil Rule 13-1(1)) | Draft chambers order terms |
| `05_Authority_Kalin_v_Campbell.txt` | Case Law Authority | Full-text judgment (PD-72 & Rule 27 compliant) |
| `manifest.json` | Binder Ingestion Metadata | Case style of cause, registry, ordered document array |

---

## Prompt Library

Use the ready-to-run prompt templates in [`prompts/`](prompts/):
- **[`generate_bc_chambers_filings_prompt.md`](prompts/generate_bc_chambers_filings_prompt.md)**: Full LLM prompt for drafting authentic BC chambers documents (Commercial Discovery Rule 7-1, Pleading Amendments Rule 6-1, Family Support Rule 10-6, Substituted Service Rule 4-4).

---

## Dynamic Chambers Motion Synthesis (Custom Agent Pattern)

When synthesizing custom chambers applications beyond the default discovery preset (e.g., interim injunctions, pleading amendments under Rule 8-1, or family law motions), agents can dynamically emit custom filing files (`.txt` or `.pdf`) and an accompanying `manifest.json`.

### Proven 20/20 Compliant Manifest Schema:
```json
{
  "court": "Supreme Court of British Columbia",
  "registry": "Vancouver",
  "file_number": "S-260606",
  "matter_type": "Interim Chambers Application (Rule 8-1)",
  "plaintiff": "Alex Morgan",
  "defendant": "Cedar Quay Developments Ltd.",
  "application_date": "November 15, 2026",
  "time_estimate": "30 minutes",
  "documents": [
    {
      "item_num": 1,
      "title": "Form 32 Notice of Application of Alex Morgan",
      "short_title": "Notice of Application",
      "filename": "01_Notice_of_Application.txt"
    },
    {
      "item_num": 2,
      "title": "Form 33 Application Response of Cedar Quay Developments Ltd.",
      "short_title": "Application Response",
      "filename": "02_Application_Response.txt"
    },
    {
      "item_num": 3,
      "title": "Form 35 Affidavit of Alex Morgan",
      "short_title": "Affidavit of Alex Morgan",
      "filename": "03_Affidavit_of_Alex_Morgan.txt",
      "exhibits": [
        {
          "letter": "A",
          "description": "Development Agreement Excerpt",
          "rel_page": 1
        },
        {
          "letter": "B",
          "description": "Records Migration Notice",
          "rel_page": 2
        }
      ]
    },
    {
      "item_num": 4,
      "title": "Form 35 Draft Order",
      "short_title": "Draft Order",
      "filename": "04_Draft_Order.txt"
    },
    {
      "item_num": 5,
      "title": "RJR-MacDonald Inc. v. Canada, [1994] 1 S.C.R. 311",
      "short_title": "RJR-MacDonald Inc. v. Canada",
      "filename": "05_Authority_RJR-MacDonald.txt"
    }
  ]
}
```

> [!TIP]
> **Exhibit Sub-Bookmarks for 20/20 PASS (`RULE-18`):**  
> Specifying `"exhibits"` with `"rel_page"` offsets under the affidavit entry instructs the binder compiler to generate nested child bookmarks (`Exhibit A - ...`, `Exhibit B - ...`). This guarantees that `RULE-18` achieves a 100% `PASS` with zero soft warnings.

---

## Workflow

1. Run `generating_court_documents.py` specifying the target destination and matter type.
2. Verify that all 5 filing files and `manifest.json` are generated.
3. Feed the resulting directory directly into the binder assembly step.

---

## Verification

Run test generation and verify non-zero byte size on all files:

```bash
python3 .apm/skills/managing-court-binders/scripts/generating_court_documents.py \
  --output-dir /tmp/test_inputs \
  --matter-type discovery
ls -lh /tmp/test_inputs
```
