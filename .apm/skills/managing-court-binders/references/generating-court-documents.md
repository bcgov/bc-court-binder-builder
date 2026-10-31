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
