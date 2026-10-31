# GitHub Copilot Instructions for BC Court Electronic Binder Builder

Welcome to **bc-court-binder-builder**. This repository provides an AI-native legal-ops compilation pipeline that builds, stamps, bookmarks, and pre-flight certifies Electronic Application Records and Books of Authorities for the Supreme Court of British Columbia and Court of Appeal under Practice Direction 72 (PD-72), Practice Direction 73 (PD-73), and Court Services Online (CSO) rules.

## Repository Overview & Architecture

- **Primary Skill:** `managing-court-binders` located at `.apm/skills/managing-court-binders/` (and deployed globally to `~/.agents/skills/managing-court-binders/`).
- **Core Pipeline Scripts:**
  - `managing_court_binders.py`: Master lifecycle driver (`--mode setup`, `--mode assemble`, `--mode validate`, `--mode generate`, `--mode all`, `--interactive`).
  - `assembling_court_binders.py`: Two-pass foliation math, Form 22 Style of Cause Title Page, 4-column Index, `/Border [0 0 0]` invisible rectangle GoTo hyperlinks, and `/PageLabels` catalog configuration.
  - `validating_court_binders.py`: 20-gate statutory pre-flight audit engine (3-tier severity: `HARD_STOP`, `SOFT_WARNING`, `PASS`).
  - `generating_court_documents.py`: Synthetic test document generator and manifest compiler.

## Copilot Execution Guidance

When a user in GitHub Copilot asks you to assist with court binders:

1. **When asked to "Check environment" or "Set up dependencies":**
   Execute:
   ```bash
   python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode setup
   ```
2. **When asked to "Create a court binder" or "Assemble an application record":**
   Execute:
   ```bash
   python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
     --mode assemble \
     --inputs <input-folder> \
     --output <output-pdf-path>
   ```
3. **When asked to "Validate this court submission" or "Audit court binder":**
   Execute:
   ```bash
   python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
     --mode validate \
     --output <target-pdf-path>
   ```
   Present the full 20-rule compliance scorecard with Hard Stops, Soft Warnings, and Final Verdict.
4. **When asked to "Run complete test loop":**
   Execute:
   ```bash
   python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode all
   ```

## Key Statutory Invariants (Must Never Violate)
- Sequential visible folios begin at **Page 1 on Tab 1** (Notice of Application).
- Title Page (Item 1) and Index (Item 2) are unnumbered (carry `/PageLabels` style `None`).
- Folios must be top-center ($x \approx 290\text{ pt}, y \approx 760\text{ pt}$), $14\text{--}16\text{ pt}$ Bold Helvetica.
- Index links must be `/Border [0 0 0]` (invisible) and `/H /N` (no highlight box).
- Total file size must remain strictly under $50\text{ MB}$.
