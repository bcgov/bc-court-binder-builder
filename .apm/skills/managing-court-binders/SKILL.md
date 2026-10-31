---
name: managing-court-binders
description: >-
  Compiles, stamps, bookmarks, and audits BC Supreme Court and Court of Appeal electronic application records and books of authorities. Use when generating synthetic filings, assembling court binders, or auditing against PD-72 and CSO compliance gates.
argument-hint: "[generate|assemble|validate|all] [--inputs <dir>] [--output <file>]"
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
| `generate` | Creates synthetic multi-page chambers filings and `manifest.json` | `python3 scripts/managing_court_binders.py --mode generate` |
| `assemble` | Compiles two-pass folios, index table, bookmarks, and links | `python3 scripts/managing_court_binders.py --mode assemble` |
| `validate` | Audits PDF against 20 court quality gates (CSO 50 MB, outlines) | `python3 scripts/managing_court_binders.py --mode validate` |
| `all` | Runs closed-loop lifecycle (generate $\to$ assemble $\to$ audit) | `python3 scripts/managing_court_binders.py --mode all` |

## Quick start

Run the unified lifecycle driver from repository root:

```bash
# Full end-to-end run (generate, compile, audit)
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode all

# Run individual modes
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode assemble --inputs inputs/01-commercial-discovery --output output/01-commercial-discovery/Application_Record.pdf
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode validate --output output/01-commercial-discovery/Application_Record.pdf
```

## Workflow

1. **Intake / Generation**: Ingest case documents or generate test filings via `--mode generate`.
2. **Assembly**: Execute two-pass continuous foliation and bookmark outline synthesis via `--mode assemble`.
3. **Verification**: Audit the output against the 20 statutory quality gates via `--mode validate`.

## Verification

```bash
# Verify 20-gate compliance
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode validate
```

Routing tests live in [evals/evals.json](evals/evals.json).

## References

- Sub-skill procedures: [generating-court-documents](references/generating-court-documents.md) • [assembling-court-binders](references/assembling-court-binders.md) • [validating-court-binders](references/validating-court-binders.md) • [chambers-prompts](references/prompts/generate_bc_chambers_filings_prompt.md)
- Legal standards: [cso-guide-april-2026](references/cso_application_record_guide_april2026.md) • [court-practice-directions](references/court_practice_directions.md) • [pdf-technical-instructions](references/pdf_instructions.md) • [paralegal-workflow](references/paralegal_video_workflow.md)
