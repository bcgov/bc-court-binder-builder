---
name: managing-court-binders
description: >-
  Builds, compiles, continuously foliates, bookmarks, and pre-flight audits BC Supreme Court and Court of Appeal electronic court binders, application records (PD-72), virtual chambers records (PD-73), and books of authorities. Use when asked to "create a court binder", "assemble an application record", "compile court documents", "validate this court submission", "pre-flight check court record", "check PD-72 compliance", or verify filings for Court Services Online (CSO).
argument-hint: "[assemble|validate|setup|all|generate] [--inputs <dir>] [--output <file>]"
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Managing Court Binders (`managing-court-binders`)

Automates compilation, continuous foliation, hyperlinked index generation, bookmarking, and 20-gate statutory auditing for British Columbia court application records under Practice Direction 72 (PD-72), Practice Direction 73 (PD-73), and Court Services Online (CSO) rules.

## Contents

- [Constraints](#constraints) • [Modes](#modes) • [Quick start](#quick-start) • [Workflow](#workflow) • [Verification](#verification) • [References](#references)

## Constraints

1. **Self-contained**: All scripts and legal reference manuals reside within this skill; no symlinks or external hubs.
2. **Deterministic execution**: Two-pass folio math, invisible rectangle links (`/Border [0 0 0]`, `/H /N`), and 20 court quality gates run deterministically.
3. **Statutory compliance**: Conforms strictly to BC Supreme Court Civil Rules (Forms 32, 33, 35), PD-72 Appendix A, and the April 2026 CSO Guide.
4. **Lean router**: `SKILL.md` is under 80 lines; comprehensive details live in [references/](references/).

## Modes

| Mode | Purpose | Script Command |
| :--- | :--- | :--- |
| `assemble` | **Primary 1**: Compiles two-pass folios, index table, bookmarks, and links | `python3 scripts/managing_court_binders.py --mode assemble` |
| `validate` | **Primary 2**: Audits PDF against 20 court quality gates (CSO 50 MB, outlines) | `python3 scripts/managing_court_binders.py --mode validate` |
| `interactive` | Guided prompt wizard asking user for operation and paths | `python3 scripts/managing_court_binders.py --interactive` |
| `setup` | Environment readiness and automated dependency install | `python3 scripts/managing_court_binders.py --mode setup` |
| `all` | Closed-loop demo (generate sample $\to$ assemble $\to$ audit) | `python3 scripts/managing_court_binders.py --mode all` |
| `generate` | Creates synthetic multi-page chambers filings and `manifest.json` | `python3 scripts/managing_court_binders.py --mode generate` |

## Quick start

Execute the driver script located in this skill's `scripts/` directory:

```bash
# Locate driver script (e.g. .claude/skills/managing-court-binders/scripts/managing_court_binders.py
# or ~/.claude/skills/managing-court-binders/scripts/managing_court_binders.py)
DRIVER="<skill-dir>/scripts/managing_court_binders.py"

# Setup & Dependency Check (auto-installs missing packages):
python3 "$DRIVER" --mode setup

# Case 1 (Most Common): Assemble court binder from document folder
python3 "$DRIVER" --mode assemble --inputs inputs/01-commercial-discovery --output output/Application_Record.pdf

# Case 2 (Most Common): Validate / audit an assembled binder PDF against 20 court rules
python3 "$DRIVER" --mode validate --output output/Application_Record.pdf

# Interactive wizard (prompts for action and paths)
python3 "$DRIVER" --interactive
```

## Workflow

When invoked without explicit flags (e.g. bare `/managing-court-binders`), conduct an interactive conversational intake:
1. Prompt the operator to select: **Case 1 (Assemble Application Record)**, **Case 2 (Validate Existing PDF)**, or **Case 3 (Demo Test Loop)**.
2. If assembling: prompt for input folder path, inspect files, confirm statutory filing sequence (Form 32 $\to$ Form 33 $\to$ Form 35 affidavits with exhibits $\to$ Draft Order), compile, and immediately execute the 20-gate pre-flight audit.
3. If validating: prompt for target PDF path and display the complete 20-gate compliance scorecard.

## Verification

```bash
# Verify 20-gate compliance
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode validate
```

Routing tests live in [evals/evals.json](evals/evals.json).

## References

- Sub-skill procedures: [generating-court-documents](references/generating-court-documents.md) • [assembling-court-binders](references/assembling-court-binders.md) • [validating-court-binders](references/validating-court-binders.md) • [filename-conventions](references/filename-conventions.md) • [environment-setup](references/environment-setup.md) • [chambers-prompts](references/prompts/generate_bc_chambers_filings_prompt.md)
- Legal standards: [cso-guide-april-2026](references/cso_application_record_guide_april2026.md) • [court-practice-directions](references/court_practice_directions.md) • [pdf-technical-instructions](references/pdf_instructions.md) • [paralegal-workflow](references/paralegal_video_workflow.md)
