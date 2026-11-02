---
name: managing-court-binders
description: >-
  Builds, compiles, continuously foliates, bookmarks, and pre-flight audits BC Supreme Court and Court of Appeal electronic court binders, application records (PD-72), virtual chambers records (PD-73), and books of authorities. Use when asked to "create a court binder", "assemble an application record", "compile court documents", "validate this court submission", "pre-flight check court record", "check PD-72 compliance", verify filings for Court Services Online (CSO), or get help registering, logging on and e-filing an application record on CSO.
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
4. **Lean router**: `SKILL.md` is under 90 lines; comprehensive details live in [references/](references/).

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
   - **Case details first.** If the folder has no `manifest.json`, ask for the registry, court file number, applicant/plaintiff, respondent/defendant and hearing date (time estimate and counsel are optional; leave them off if unknown) and pass them as `--registry`, `--file-number`, `--plaintiff`, `--defendant`, `--hearing-date` (plus `--time-estimate` if given), which write `manifest.json`. Never guess them or reuse sample values such as `S-240123`.
   - **Where it goes.** Keep source filings in `inputs/<matter>/` and save binders in `output/<matter>/` as `Application_Record_<matter>_<DDMmmYYYY>.pdf` ([naming](references/filename-conventions.md)). Never overwrite an existing binder.
3. If validating: prompt for target PDF path and display the complete 20-gate compliance scorecard.

For generation or assembly requests, use any input and output paths the user already supplied. If an output location is missing, ask where to save the generated source filings and/or assembled binder before creating those outputs. Resolve relative paths against the active workspace (which may be a Copilot or other agent worktree), not an assumed main checkout. After writing the binder, verify that the file exists and report its absolute path as a clickable Markdown link so the user can open it. State plainly when the file is inside a worktree.

### CSO account and e-filing help

If the user asks how to register for, log on to, or file on CSO, follow [cso-account-and-efiling](references/cso-account-and-efiling.md): ask the account, log-on and credit-card questions in order and give only the addresses in [cso_links.json](references/cso_links.json). Guide only; never enter credentials or payment details or submit for the user.

## Verification

```bash
# Verify 20-gate compliance
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode validate
```

Add `--strict` to `--mode validate` to treat `SOFT_WARNING` as a failure (exit code 1). Routing tests live in [evals/evals.json](evals/evals.json).

## References

- Sub-skill procedures: [generating-court-documents](references/generating-court-documents.md) • [assembling-court-binders](references/assembling-court-binders.md) • [validating-court-binders](references/validating-court-binders.md) • [filename-conventions](references/filename-conventions.md) • [environment-setup](references/environment-setup.md) • [chambers-prompts](references/prompts/generate_bc_chambers_filings_prompt.md)
- CSO filing help: [cso-account-and-efiling](references/cso-account-and-efiling.md) • [cso_links.json](references/cso_links.json)
- Legal standards: [cso-guide-april-2026](references/cso_application_record_guide_april2026.md) • [court-practice-directions](references/court_practice_directions.md) • [pdf-technical-instructions](references/pdf_instructions.md) • [paralegal-workflow](references/paralegal_video_workflow.md)
