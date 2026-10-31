# CLAUDE.md — Agent Working Instructions for bc-court-binder

Refer to [`AGENTS.md`](AGENTS.md) for full project invariants, statutory authorities, and the 20 BC court quality gates.

---

## ⚡ Quick Start: Running Skills Directly

From repository root:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run closed-loop generation, compilation, and compliance audit:
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode all

# 3. Or run discrete operational modes:
# Generate input filings
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode generate \
  --inputs inputs/04-creditor-execution \
  --matter-type discovery

# Assemble into an electronic court binder
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode assemble \
  --inputs inputs/04-creditor-execution \
  --output output/04-creditor-execution/Application_Record_Creditor_Execution.pdf

# Pre-flight audit against the 20 BC Court quality gates
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode validate \
  --output output/04-creditor-execution/Application_Record_Creditor_Execution.pdf
```

---

## ⚖️ Core Invariants for Changes

- **The 20 Quality Gates Must Pass (100%)**: Never mark work complete if `validating_court_binders.py` reports any `HARD_STOP` or `SOFT_WARNING`.
- **Top-Center Folios**: Always stamp top-center in Arial/Helvetica Bold 14–16 pt on substantive pages. Cover & Index remain unnumbered.
- **Synchronized `/PageLabels`**: Always maintain ISO 32000 Table 159 empty dict `0 << >>` for front matter so page searching aligns with printed folios.
- **Invisible Rectangle Links**: Index lines must use `/Border [0 0 0]`, `/H /N`, and universal GoTo `/A << /S /GoTo /D [target R /FitH 792] >>` actions.
