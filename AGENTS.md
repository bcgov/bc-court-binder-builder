# AGENTS.md — Developer & AI Agent Guidelines for bc-court-binder

This file binds every human contributor and AI coding agent working in this repository. It defines environment setup, dependency management, execution workflows, and compliance quality gates.

---

## 1. Project Mission & Architecture

`bc-court-binder` is an enterprise legal-ops compilation and pre-flight auditing pipeline for the Supreme Court of British Columbia and the Court of Appeal for British Columbia. It automates:
1. **Form 22 Style of Cause Title Page** (Item 1)
2. **Columnar Legal Index Table** (Item 2) with invisible rectangle GoTo hyperlinks
3. **Continuous Top-Center Folio Stamping** ($15\text{ pt}$ Bold Arial/Helvetica)
4. **Hierarchical Bookmarks Panel** with party disambiguation and nested exhibits
5. **Digital Page Labels (`/PageLabels`)** synchronized with visual folios
6. **Pre-Flight Compliance Auditing** against 20 statutory quality gates

---

## 2. Dependency Setup: Consuming the PdfCraft SDK

This repository consumes the core document processing engine from [`richfrem/pdfcraft`](https://github.com/richfrem/pdfcraft).

### 2.1 Python Environment (Primary for Agent Skills)
Agents and scripts run under Python 3.9+.

```bash
# 1. Initialize virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# 2. Install dependencies and native PdfCraft SDK
pip install -r requirements.txt
```

#### How `requirements.txt` Resolves the Native SDK:
`requirements.txt` automatically resolves the pre-compiled native PyO3 wheel from the latest engine release based on your operating system:
* **macOS (Apple Silicon arm64)**: `pdfcraft-0.5.0-cp313-cp313-macosx_11_0_arm64.whl`
* **Windows (win_amd64)**: `pdfcraft-0.5.0-cp313-cp313-win_amd64.whl`
* **Fallback / Development Source**: If pre-compiled wheels are not yet reachable, agents fall back to pure-Python/pypdf vector operations or local pip install:
  ```bash
  pip install "git+https://github.com/richfrem/pdfcraft.git#subdirectory=sdks/python"
  ```

### 2.2 Rust Environment (Optional CLI & SDK Runner)
When executing or modifying Rust code in `src/main.rs`:

```toml
[dependencies]
pdfcraft-sdk = { git = "https://github.com/richfrem/pdfcraft", branch = "main" }
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }

# Local development override (when working side-by-side with local pdfcraft clone):
[patch."https://github.com/richfrem/pdfcraft"]
pdfcraft-sdk = { path = "../pdfcraft/crates/sdk" }
```

Build and execute:
```bash
cargo check
cargo run
```

---

## 3. Agent Tool & Skill Execution Workflows

Agents must use the modular `.apm/skills` scripts to generate, assemble, and validate binders headlessly:

```mermaid
flowchart LR
    G["generating-court-documents<br/>(inputs/)"] --> A["assembling-court-binders<br/>(output/*.pdf)"]
    A --> V["validating-court-binders<br/>(20 Gates)"]
    V -->|20/20 PASS| S["Approved for CSO"]
```

### Step 1: Synthesize Input Filings (If generating a test case)
```bash
python3 .apm/skills/generating-court-documents/scripts/generating_court_documents.py \
  --output-dir inputs/01-commercial-discovery \
  --matter-type discovery
```

### Step 2: Assemble the Electronic Court Binder
```bash
python3 .apm/skills/assembling-court-binders/scripts/assembling_court_binders.py \
  --inputs inputs/01-commercial-discovery \
  --output output/01-commercial-discovery/Application_Record.pdf
```

### Step 3: Run the Pre-Flight Compliance Gate Audit
```bash
python3 .apm/skills/validating-court-binders/scripts/validating_court_binders.py \
  --file output/01-commercial-discovery/Application_Record.pdf
```
To obtain structured machine-readable JSON for agent receipt verification:
```bash
python3 .apm/skills/validating-court-binders/scripts/validating_court_binders.py \
  --file output/01-commercial-discovery/Application_Record.pdf \
  --json
```

---

## 4. Quality Invariants: The 20 Mandatory Court Gates

A change is **not done** and must **never be committed** if any court quality gate fails:

- `RULE-00` (**HARD_STOP**): Document must be unencrypted without password protection.
- `RULE-01` (**HARD_STOP**): Must be a single consolidated PDF volume.
- `RULE-02` (**HARD_STOP**): File size must not exceed $50.0\text{ MB}$ ($52,428,800\text{ bytes}$).
- `RULE-03` (**SOFT_WARNING**): Initial View must set `/PageMode /UseOutlines` to display bookmarks by default.
- `RULE-04` (**HARD_STOP**): Item 1 must be Form 22 / Form 30.001 Style of Cause Title Page.
- `RULE-05` (**HARD_STOP**): Item 2 must be the Numbered Index positioned before substantive tabs.
- `RULE-06` (**HARD_STOP**): Every listed item in the Index must feature exact calculated page folios.
- `RULE-07` (**SOFT_WARNING**): Index entries must have active `/Subtype /Link` annotations.
- `RULE-08` (**SOFT_WARNING**): Link appearance must be `Invisible Rectangle` (`/Border [0 0 0]`), Highlight: `None` (`/H /N`).
- `RULE-09` (**SOFT_WARNING**): Links must feature universal GoTo actions (`/A << /S /GoTo /D [target R /FitH 792] >>`) jumping to top view.
- `RULE-10` (**HARD_STOP**): Page numbers must be stamped top-center ($x \approx 290\text{ pt}, y \approx 760\text{ pt}$, within top $100\text{ pt}$ margin).
- `RULE-11`–`RULE-13` (**SOFT_WARNING**): Page numbers must use Arial/Helvetica Bold, $14\text{--}16\text{ pt}$.
- `RULE-14` (**HARD_STOP**): Printed folio `1` must begin on Tab 1 (Notice of Application); Title Page & Index are unnumbered.
- `RULE-15` (**HARD_STOP**): Catalog `/PageLabels` must be synchronized with visual folios.
- `RULE-16` (**SOFT_WARNING**): Front matter page labels set to `None` (`0 << >>`).
- `RULE-17` (**HARD_STOP**): Bookmarks must be descriptive with party names; generic titles (`Page 1`, `Scan 001`) are rejected.
- `RULE-18` (**HARD_STOP**): Affidavit exhibits must be nested as child bookmarks; vector text must pass Shannon character entropy ($H \ge 3.0$); legal authorities must be included as full-text PDF pages (never external web links).
- `RULE-19` (**SOFT_WARNING**): Pages must conform to standard North American Letter dimensions ($8.5 \times 11\text{ inches}$, $612 \times 792\text{ pt}$).

---

## 5. Security, Clean-Room & Privacy Policies

1. **Synthetic Fixtures Only**: Never commit real litigant PII, confidential case materials, real bank statements, or sensitive court filings. All test cases must use synthetic, fictitious parties and docket numbers.
2. **Never Crash**: Ingestion of malformed PDFs or bad manifest arguments must return a descriptive `Result` or exit code with remediation advice—never an unhandled panic.
3. **Statutory Integrity**: Reference all court rules back to official publications in `references/` (`PD-72`, `PD-73`, and the April 2026 CSO Guide).
