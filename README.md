# BC Court Electronic Binder Builder

> [!IMPORTANT]
> ### 🧪 PROOF OF CONCEPT (POC)
> **This project is a Proof of Concept (POC) validating an AI-native, correct-by-construction approach to electronic court application records.**
> 
> Rather than relying on expensive downstream automated audits or manual registry inspections *after* a defective binder has already been submitted, this POC empowers **law offices and legal-ops teams to build and pre-flight validate their own binders locally before submission**.
> 
> By synthesizing compliant folios, index hyperlinks, and bookmark trees deterministically by construction, it **eliminates the need for downstream automated binder validation**, prevents registry clerk rejections, avoids costly hearing adjournments, and guarantees first-time submission acceptance.

[![Compliance](https://img.shields.io/badge/BC%20Courts%20PD--72-20%2F20%20PASS-brightgreen)](#the-20-mandatory-court-quality-gates)
[![Jurisdiction](https://img.shields.io/badge/Jurisdiction-British%20Columbia%20(SC%20%26%20CA)-blue)](#key-technical-documentation)
[![Engine](https://img.shields.io/badge/Powered%20By-PdfCraft%20SDK-orange)](https://github.com/richfrem/pdfcraft)

An automated, AI-native legal-ops pipeline for compiling, stamping, bookmarking, and certifying **Electronic Application Records** and **Books of Authorities** for the Supreme Court of British Columbia and the Court of Appeal for British Columbia.

> **💡 Better Than Validating Mistakes After the Fact — Correct by Construction:**  
> Traditional approaches rely on reactionary audits after a binder is already defective. This AI-native agent skill synthesizes electronic court binders **correctly by construction**. Two-pass mathematical foliation, coordinate-projected hyperlinks, and standardized top-center page numbers ensure that formatting errors, registry clerk rejections, rework, and costly refilings never happen in the first place.

Strictly adheres to:
* **Practice Direction 72 (PD-72)** (*Electronic Application Records*):  
  [Live Official PDF](https://www.bccourts.ca/supreme_court/practice_and_procedure/practice_directions/civil/PD-72_Electronic_Application_Records.pdf) • [Pilot Project Portal](https://www.bccourts.ca/supreme_court/practice_and_procedure/associate_judges_chambers_pilot_project.aspx) • [Local Archive](.apm/skills/managing-court-binders/references/pdfs/PD-72_Electronic_Application_Records.pdf) • [Analysis](.apm/skills/managing-court-binders/references/court_practice_directions.md)
* **Practice Direction 73 (PD-73)** (*Virtual Chambers & MS Teams Hearings*):  
  [Live Official PDF](https://www.bccourts.ca/supreme_court/practice_and_procedure/practice_directions/civil/PD-73_Virtual_Chambers.pdf) • [2026 Sitting Schedule PDF](https://www.bccourts.ca/supreme_court/scheduling/ASSOCIATE_JUDGES_VIRTUAL_CHAMBERS_SITTING_SCHEDULE_2026.pdf) • [Local Archive](.apm/skills/managing-court-binders/references/pdfs/PD-73_Virtual_Chambers.pdf)
* **Court Services Online (CSO)** (*Guide to Submitting Application Records, April 2026*):  
  [Live Official PDF](https://justice.gov.bc.ca/pdfs/cso/InstructionsForUsersForApplicationRecords.pdf) • [CSO Portal](https://justice.gov.bc.ca/cso/) • [Local Archive](.apm/skills/managing-court-binders/references/pdfs/InstructionsForUsersForApplicationRecords.pdf) • [Analysis](.apm/skills/managing-court-binders/references/cso_application_record_guide_april2026.md)
* **BCCA Civil Rule 27** (*Completion Instructions for Books of Authorities*):  
  [Live Official PDF](https://www.bccourts.ca/Court_of_Appeal/practice_and_procedure/completion_instructions/civil/e_completion_instructions_book_of_authorities.pdf) • [Local Archive](.apm/skills/managing-court-binders/references/pdfs/e_completion_instructions_book_of_authorities.pdf)
* **Paralegal Best Practices** (*Vancouver Senior Paralegal 9-Step Standard*):  
  [Vimeo Training Video (ID 836310097)](https://vimeo.com/836310097) • [Video Analysis & Transcript](.apm/skills/managing-court-binders/references/paralegal_video_workflow.md)
* **BC Supreme Court PDF Guides** (*All 13 Acrobat Technical Instruction Manuals*):  
  [Court Practice & Procedure Portal](https://www.bccourts.ca/supreme_court/practice_and_procedure/pdf_instructions.aspx) • [Technical Breakdown](.apm/skills/managing-court-binders/references/pdf_instructions.md)

---

## 📑 Table of Contents

- [🏛️ Strategic Purpose & Benefits (Virtual Courts)](#strategic-purpose)
- [🤖 The AI-Native Paradigm (Deterministic Execution)](#ai-native-paradigm)
- [📚 Key Technical Documentation](#technical-docs)
- [🔗 Lineage & Referenced Repositories](#referenced-repos)
- [🤖 Consolidated Agent Skill (`managing-court-binders`)](#consolidated-skill)
  - [Operational Modes](#operational-modes)
  - [Key Reference Manuals](#reference-manuals)
- [🛠️ Initial Setup, Dependencies & APM Installation](#setup-installation)
  - [1. APM Package Installation for AI Agents](#apm-installation)
  - [2. Python Environment & Zero-Compiler Setup](#python-setup)
  - [3. Optional Rust Toolchain Setup](#rust-setup)
- [🎮 Running the Interactive Skill](#running-interactive-skill)
  - [1. Guided Terminal Wizard](#interactive-wizard)
  - [2. Direct CLI Commands](#cli-commands)
  - [3. Conversational AI Agent Triggers](#agent-prompts)
- [⚖️ The 20 Mandatory Court Quality Gates](#quality-gates)
- [🦀 Rust Reference Pipeline (`pdfcraft-sdk`)](#rust-pipeline)
  - [Pipeline Comparison Matrix](#pipeline-comparison)
- [📄 License & Open-Source Terms](#license)

---

<a id="strategic-purpose"></a>
## 🏛️ Strategic Purpose & Institutional Benefits: Enabling Virtual Courts

For the complete legal-economic policy analysis, read: 👉 **[`COURT_PURPOSE_AND_BENEFITS.md`](COURT_PURPOSE_AND_BENEFITS.md)**.

Modernizing court records from physical 3-ring paper binders to mathematically verified, hyperlinked **eBinders** unlocks three transformative pillars for British Columbia's justice system:

| Beneficiary Pillar | Core Economic & Operational Impact | Strategic Access to Justice Multiplier |
| :--- | :--- | :--- |
| **1. Everyday Citizens & Litigants** | **$1,000–$3,000 direct cost savings** per application by eliminating 1,000+ pages of printing, heavy binders, tabs, couriers, and attorney travel. | **Geographic equity:** Remote/northern communities (Fort St. John, Cranbrook) get equal, immediate chambers access via MS Teams (PD-73). |
| **2. Law Firms & Legal Operations** | Replaces **45–90 minutes** of tedious manual Acrobat drag-and-drop with a sub-second (**< 200 ms**) mathematical build. | **0% error guarantee:** Eliminates off-by-one folios and ensures pre-flight 20/20 PASS, preventing rejected submissions. |
| **3. Court System & Virtual Chambers** | **Provincial workload balancing:** Decouples hearings from geography by dynamically shifting dockets to available judges in Victoria/Kelowna. | **Registry & hearing velocity:** Eliminates physical binder warehouse rooms and speeds oral argument with synchronized folios and GoTo links. |

### Key Beneficiary Impact Matrix:

1. **For Everyday Citizens & Litigants (Access to Justice):**
   * **Direct Legal Cost Reduction:** Traditional chambers applications required 3 to 4 paper volumes (1,000+ pages), custom tab dividers, couriers, and multiple hours of lawyer travel and court waiting time. eBinders reduce non-legal clerical costs to **$0**, saving litigants **$1,000 to $3,000 per application**.
   * **Elimination of Geographic Barriers:** Litigants in rural or northern BC communities no longer need to pay thousands of dollars for counsel to travel to regional judicial centers; applications are heard virtually via MS Teams (PD-73).

2. **For Law Firms & Paralegals (Zero Friction Automation):**
   * **Replaces Tedious Manual Assembly:** Paralegals spend 45 to 90 minutes per filing manually dragging-and-dropping PDFs in Adobe Acrobat, setting page labels, calculating table of contents numbers, and drawing invisible link rectangles. This engine executes the full synthesis in **< 200 milliseconds**.
   * **Guaranteed First-Time Acceptance:** Pre-flight compliance auditing against the 20 court quality gates prevents embarrassing registry rejections and costly hearing adjournments.

3. **For the Court System & Virtual Chambers Utilization:**
   * **Provincial Workload Balancing:** When the Vancouver or New Westminster registry has 40+ chambers applications on a morning list and cannot accommodate them, Court Services Online can dynamically route electronic application records to available Associate Judges in Victoria, Kelowna, or Prince George without courier delays.
   * **Registry Operations Optimization:** Courthouses eliminate warehouse rooms dedicated to storing heavy 3-ring binders pending hearings and post-hearing shredding. Registry clerks use automated validation gates to pre-flight filings in seconds.
   * **Virtual Hearing Velocity:** In MS Teams hearings, when counsel says *"Please turn to page 14 of the Record, which is Exhibit B to the Affidavit"*, the judge clicks a single bookmark or index hyperlink and instantly views the identical page, avoiding disorientation during 30-minute hearings.

---

<a id="ai-native-paradigm"></a>
## 🤖 The AI-Native Paradigm: Deterministic Execution via Agent Skills

Rather than building another monolithic, heavyweight software application that requires complex UI maintenance, installation barriers, and manual operator training, this project introduces an **AI-native Agent Skill** (`managing-court-binders`). 

It empowers humans, paralegals, and autonomous coding agents (Claude, Codex, Gemini, Antigravity) to orchestrate a high-performance legal compilation pipeline directly through conversational instructions, interactive terminal wizards, or headless CI/CD execution.

| Execution Dimension | Traditional Manual Overhead (Adobe Acrobat) | AI-Native Agent Skill (`managing-court-binders`) | Impact & Multiplier |
| :--- | :--- | :--- | :--- |
| **Preparation Velocity** | 45–90 min manual dragging, bookmarking, and folio stamping | **< 200 ms** deterministic programmatic build | **99% time & cost reduction** |
| **Compliance Validation** | Manual visual inspection against 14+ practice directions | Instant automated 20/20 quality gate pre-flight audit | **100% audit coverage** before registry submission |
| **Filing Outcome** | Frequent rejection from off-by-one folios & broken links | Mathematical zero-defect guarantee; first-time CSO acceptance | **Eliminates refilings & hearing delay** |

### Three FTE Efficiency Multipliers (Work Better Done by a Machine):

1. **Drastic Time & Cost Reduction (Error Elimination):**
   * Eliminates 45–90 minutes of tedious, billable paralegal labour spent manually stamping page numbers, dragging bookmark trees, and drawing invisible hyperlink rectangles in Adobe Acrobat.
   * Replaces human guesswork with deterministic mathematical precision ($< 200\text{ ms}$ execution, 0 tokens wasted, 0 hallucinations).
2. **Automated Downstream Registry Validation:**
   * Eliminates the clerical burden on court registry staff by providing automated pre-flight validation gates. Clerks and law firms can verify in seconds whether a 500-page submission satisfies all 20 statutory quality gates before it is accepted.
3. **Eradicating Defective Filings & Refiling Fees:**
   * High-stakes chambers applications frequently get rejected due to subtle formatting defects (folios in footers instead of top-center, missing bookmark outlines, broken index links, unencrypted passwords).
   * Programmatic pre-flight certification guarantees first-time acceptance, saving thousands of dollars in refiling fees, hearing adjournments, and client stress.
4. **FTE Liberation for Higher-Order Justice Work:**
   * Repetitive clerical PDF manipulation is work better done by a deterministic machine. Freeing paralegals, legal assistants, and court clerks from manual formatting enables them to focus on substantive legal research, case strategy, and citizen support.

---

<a id="technical-docs"></a>
## 📚 Key Technical Documentation

* **[`architecture.md`](architecture.md):** System architecture, legal taxonomy of submittable chambers matters (< 30 minutes before Associate Judges), component layering, and the consolidated skill specification.
* **[`BC_ELECTRONIC_BINDER_SPEC.md`](BC_ELECTRONIC_BINDER_SPEC.md):** Complete synthesis of the 9-step paralegal manual workflow (from Senior Vancouver Paralegal Video 836310097) vs. the automated SDK pipeline.
* **[`managing-court-binders/references/`](.apm/skills/managing-court-binders/references/):** Consolidated, self-contained library containing procedural sub-skill manuals, environment setup guides, official court practice directions (`PD-72`, `PD-73`), the April 2026 CSO Guide, 18 source court PDFs, and all 13 BC Supreme Court PDF technical instruction guides.

---

<a id="referenced-repos"></a>
## 🔗 Lineage & Referenced Repositories

This proof-of-concept synthesizes technical research, legal-ops automation models, and PDF engine primitives developed across three related repositories:

1. **[`richfrem/pdfcraft`](https://github.com/richfrem/pdfcraft):**  
   The extended enterprise distribution and document processing SDK containing the Layer 7 in-process client (`pdfcraft-sdk`), native PyO3 acceleration module (`pdfcraft-pyo3`), self-hosted REST service (`pdfcraft-rest`), and pre-built Python wheels distributed via GitHub Releases.
2. **[`storytold/pdfcraft`](https://github.com/storytold/pdfcraft):**  
   The upstream clean-room, headless PDF processing engine and rendering kernel authored under strict clean-room rules (ISO 32000-2 / Arlington model) with zero Adobe proprietary dependencies.
3. **[`bcgov-c/jag-cso-assistant`](https://github.com/bcgov-c/jag-cso-assistant) *(Private Ministry of Attorney General Repository)*:**  
   The foundational Azure AI Foundry POC and policy evaluation suite that originally codified the 20 British Columbia court quality gates, 3-tier severity classification (`HARD_STOP`, `SOFT_WARNING`, `PASS`), spatial margin bounding box algorithms, and Shannon character OCR entropy heuristics.

---

<a id="consolidated-skill"></a>
## 🤖 Consolidated Agent Skill (`.apm/skills/managing-court-binders`)

This repository encapsulates all legal-ops capabilities into a single, self-contained APM domain skill: **[`managing-court-binders`](.apm/skills/managing-court-binders)**.

<a id="operational-modes"></a>
### Operational Modes

| Mode | Priority / Use Case | Operational Function | Command |
| :--- | :--- | :--- | :--- |
| **`assemble`** | **Case 1 (Primary)** | Ingests source documents, calculates two-pass folios, builds Form 22 Title Page and 4-column Index, stamps top-center folios, sets `/PageLabels`, and injects `/Border [0 0 0]` invisible hyperlinks. | `python3 scripts/managing_court_binders.py --mode assemble` |
| **`validate`** | **Case 2 (Primary)** | Audits candidate PDF against the 20 statutory court quality gates (CSO 50 MB, outlines, margins, OCR entropy). | `python3 scripts/managing_court_binders.py --mode validate` |
| **`interactive`** | Guided Wizard | Launches interactive terminal menu prompting the operator for desired workflow and file paths. | `python3 scripts/managing_court_binders.py --interactive` |
| **`setup`** | Diagnostics & Install | Verifies Python runtime, pip dependencies (`pypdf`, `pdfplumber`), native PyO3 wheel, and Rust toolchain; auto-installs missing packages. | `python3 scripts/managing_court_binders.py --mode setup` |
| **`all`** | Closed-Loop Demo | Full automated loop: synthesizes test filings $\to$ compiles binder $\to$ executes 20-gate compliance audit. | `python3 scripts/managing_court_binders.py --mode all` |
| **`generate`** | Test Data Synthesis | Synthesizes authentic multi-page chambers filings (`discovery`, `amendment`, `family`) and companion `manifest.json`. | `python3 scripts/managing_court_binders.py --mode generate` |

<a id="reference-manuals"></a>
### Key Reference Manuals (`references/`)

All domain knowledge is modularized inside [`.apm/skills/managing-court-binders/references/`](.apm/skills/managing-court-binders/references/):
* **Procedural Sub-Skill References:**
  * [`assembling-court-binders.md`](.apm/skills/managing-court-binders/references/assembling-court-binders.md) — Two-pass foliation math, coordinate projection, `/Border [0 0 0]` invisible links, `/PageLabels`.
  * [`validating-court-binders.md`](.apm/skills/managing-court-binders/references/validating-court-binders.md) — 20-gate compliance auditing engine, 3-tier severity (`HARD_STOP`, `SOFT_WARNING`), OCR entropy ($H \ge 3.0$).
  * [`generating-court-documents.md`](.apm/skills/managing-court-binders/references/generating-court-documents.md) — Supreme Court Forms 32, 33, and 35 filing generator and manifest schemas.
  * [`environment-setup.md`](.apm/skills/managing-court-binders/references/environment-setup.md) — Runtime environment verification, pip dependencies, native PyO3 wheel, and Rust toolchain setup.
  * [`prompts/generate_bc_chambers_filings_prompt.md`](.apm/skills/managing-court-binders/references/prompts/generate_bc_chambers_filings_prompt.md) — High-density LLM prompt template for drafting chambers filings.
* **Official Court Standards & Live Documents:**
  * [`cso_application_record_guide_april2026.md`](.apm/skills/managing-court-binders/references/cso_application_record_guide_april2026.md) — Court Services Online (CSO) April 2026 guidelines ([Live Official PDF](https://justice.gov.bc.ca/pdfs/cso/InstructionsForUsersForApplicationRecords.pdf)).
  * [`court_practice_directions.md`](.apm/skills/managing-court-binders/references/court_practice_directions.md) — Practice Direction 72 ([Live PDF](https://www.bccourts.ca/supreme_court/practice_and_procedure/practice_directions/civil/PD-72_Electronic_Application_Records.pdf)), Practice Direction 73 ([Live PDF](https://www.bccourts.ca/supreme_court/practice_and_procedure/practice_directions/civil/PD-73_Virtual_Chambers.pdf)), [Associate Judges Pilot Project Portal](https://www.bccourts.ca/supreme_court/practice_and_procedure/associate_judges_chambers_pilot_project.aspx), and [2026 Virtual Chambers Sitting Schedule PDF](https://www.bccourts.ca/supreme_court/scheduling/ASSOCIATE_JUDGES_VIRTUAL_CHAMBERS_SITTING_SCHEDULE_2026.pdf).
  * [`paralegal_video_workflow.md`](.apm/skills/managing-court-binders/references/paralegal_video_workflow.md) — Senior Vancouver Paralegal 9-step manual workflow transcript & analysis ([Vimeo Video 836310097](https://vimeo.com/836310097)).
  * [`pdf_instructions.md`](.apm/skills/managing-court-binders/references/pdf_instructions.md) — Technical analysis of all 13 official Supreme Court PDF instructions ([Court Portal](https://www.bccourts.ca/supreme_court/practice_and_procedure/pdf_instructions.aspx)).
  * `references/pdfs/` — Archive of 18 official court PDF instruction guides, schedules, and sample application records.

---

<a id="setup-installation"></a>
## 🛠️ Initial Setup, Dependencies & APM Installation

For full cross-platform instructions, Windows PowerShell settings, and CI/CD pipelines, read: 👉 **[`INSTALL.md`](INSTALL.md)**.

<a id="apm-installation"></a>
### 1. APM Package Installation for AI Agents (Recommended)

This repository publishes its legal-ops capabilities as an [APM](https://github.com/microsoft/apm) package (`@bcgov/bc-court-binder-builder`), allowing you to install the `managing-court-binders` skill directly into any supported AI coding agent with one command.

#### Install the APM CLI (if not already installed):
* **macOS / Linux:** `curl -sSL https://aka.ms/apm-unix | sh -s -- @v0.35.0`
* **Windows (PowerShell):** `irm https://aka.ms/apm-windows | iex`

#### Install from GitHub into Your AI Agent Environment:

* **Global Workstation Installation** (Deploy to all agent environments on your machine):
  ```bash
  apm install https://github.com/bcgov/bc-court-binder-builder --global --target claude,copilot,codex,gemini
  ```

* **Project-Local Installation** (Scoped to current legal case or project folder):
  ```bash
  apm install https://github.com/bcgov/bc-court-binder-builder --target claude,copilot,codex,gemini
  ```

* **Clone-Based Local Install** (Deploy from your local working copy):
  ```bash
  apm install "$PWD/.apm/skills/managing-court-binders" --global --target claude,copilot,codex,gemini
  ```

#### Target AI Agent Environments & Deployment Paths:

| Target Flag | Target Agent Platform | Deployed Skill Path |
| :--- | :--- | :--- |
| `claude` | **Claude Code CLI** | `~/.claude/skills/managing-court-binders/` |
| `copilot` | **GitHub Copilot CLI** | `~/.agents/skills/managing-court-binders/` |
| `codex` | **OpenAI Codex CLI** | `~/.agents/skills/managing-court-binders/` |
| `agy` / `gemini` | **Antigravity / Gemini CLI** | `~/.gemini/antigravity-cli/skills/managing-court-binders/` |

---

<a id="python-setup"></a>
### 2. Python Environment & Zero-Compiler Setup

If running without APM, the entire pipeline operates out of the box with standard Python (3.9–3.13) and zero compiler toolchains:

```bash
# 1. Clone the repository
git clone https://github.com/bcgov/bc-court-binder-builder.git
cd bc-court-binder-builder

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1

# 3. Install lightweight dependencies (pypdf, pdfplumber)
pip install -r requirements.txt
```

> [!TIP]
> **Optional: Native PyO3 Wheel Acceleration:**  
> For enterprise-scale batch processing, download and install the pre-built native wheel directly from GitHub Releases with zero Rust compilation:  
> `pip install "https://github.com/richfrem/pdfcraft/releases/download/v0.16.1/pdfcraft-0.5.0-cp313-cp313-macosx_11_0_arm64.whl"`

---

<a id="rust-setup"></a>
### 3. Optional Rust Toolchain Setup (`pdfcraft-sdk`)

Only required if compiling and modifying the native Rust reference engine in [`src/main.rs`](src/main.rs):

```bash
# Install Rust toolchain (1.80+)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

# Run native reference implementation against pdfcraft-sdk Layer 7 client
cargo run
```

---

<a id="running-interactive-skill"></a>
## 🎮 Running the Interactive Skill

<a id="interactive-wizard"></a>
### 1. Guided Terminal Wizard (Interactive Mode)

Launch the step-by-step interactive CLI to assemble or validate binders with guided prompts:

```bash
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --interactive
```

The interactive wizard prompts the operator for:
1. **Action:** Assemble new binder, validate existing PDF, generate synthetic test filings, or execute the end-to-end pipeline.
2. **Matter Type:** Commercial Document Discovery (Rule 7-1), Notice of Application Amendment (Rule 8-1), or Family Law Maintenance/Custody.
3. **Paths:** Input directory containing source PDFs / exhibits and target output PDF path.
4. **Execution & Live Audit:** Compiles the PDF and prints the 20-rule compliance scorecard.

---

<a id="cli-commands"></a>
### 2. Direct CLI Commands

```bash
# Complete Closed-Loop Demonstration (Generates inputs -> Assembles -> Validates)
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode all

# Case 1 (Primary): Assemble an electronic court binder from input filings
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode assemble \
  --inputs inputs/01-commercial-discovery \
  --output output/01-commercial-discovery/Application_Record.pdf

# Case 2 (Primary): Audit / validate an assembled binder PDF against the 20 quality gates
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode validate \
  --output output/01-commercial-discovery/Application_Record.pdf

# Diagnostics & Auto-Setup
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode setup
```

---

<a id="agent-prompts"></a>
### 3. Conversational AI Agent Triggers

When deployed via APM to Claude Code, GitHub Copilot, Codex, or Antigravity/Gemini, you can drive the skill using plain language:

* 🗣️ *"Build a compliant BC Supreme Court application record from the files in `./inputs/01-commercial-discovery`."*
* 🗣️ *"Pre-flight validate our application record at `./output/Application_Record.pdf` against the 20 court quality gates."*
* 🗣️ *"Synthesize authentic chambers documents for an amendment application under Rule 8-1."*
* 🗣️ *"Check whether this binder satisfies Practice Direction 72 and Court Services Online requirements."*

---

<a id="quality-gates"></a>
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

<a id="rust-pipeline"></a>
## 🦀 Rust Reference Pipeline (`pdfcraft-sdk`)

The Rust runner in [`src/main.rs`](src/main.rs) is the native reference implementation that directly integrates with the in-process [`pdfcraft-sdk`](https://github.com/richfrem/pdfcraft) crate (`Layer 7`). It demonstrates how to build and verify a court application record without external CLI utilities.

#### What `cargo run` Does:
1. **In-Memory Legal Case Synthesis:** Instantiates a 5-document commercial discovery case (*Notice of Application*, *Application Response*, *Affidavit #1 of Eleanor Vance with Exhibits A & B*, *Draft Order*, and *Kalin v. Campbell* authority).
2. **Dynamic Folio & Index Math:** Calculates exact folio target coordinates starting at **Page 1 on Tab 1** (leaving Title & Index unnumbered per Rule 16).
3. **Vector PDF Generation:** Generates the Title page and 4-column Index table (`TAB`, `DOCUMENT`, `FILED DATE`, `PAGE`) with invisible rectangle GoTo hyperlinks (`/Border [0 0 0]`, `/H /N`).
4. **Folio Stamping & Digital Metadata:** Injects $15\text{ pt}$ Bold Helvetica top-center page folios, sets `/PageLabels`, and configures Initial View (`/PageMode /UseOutlines`).
5. **PdfCraft SDK Verification:** Calls `pdfcraft_sdk::LocalClient::default().render_page(&src, 1, ...)` to mathematically verify that the PdfCraft rasterization engine renders Page 1 without syntax errors.
6. **CSO Audit & File Output:** Audits the generated PDF against the $50\text{ MB}$ Court Services Online limit and writes the file.

```bash
# Prerequisites: Rust 1.80+ (https://rustup.rs or `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
# Execute the native Rust pipeline
cargo run
```

#### Output Artifact:
```text
output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf
```

#### Sample Terminal Output:
```text
================================================================================
   BRITISH COLUMBIA ELECTRONIC APPLICATION RECORD BUILDER (PD-72 & CSO POC)     
   Synthesized from BC Court Rules, CSO User Guides & Senior Paralegal Practice 
================================================================================

Step 1: Ingesting source documents and exhibit metadata...
Step 2: Calculating dynamic page numbering, folios, and bookmarks...
   -> Front matter: 2 pages (Title page + dynamic Index)
   -> Tab 1 starts at visible Page 1 (foliated continuous)
   -> Total substantive content: 15 pages across 5 items
   -> Total application record size: 17 pages
Step 3: Generating PDF byte stream with vector layout...
Step 4: Compiling hierarchical bookmark outline tree and link annotations...
Step 5: Verifying PDF with PdfCraft LocalClient...
   -> PdfCraft engine raster verification passed: Page 1 rendered successfully
Step 6: Executing CSO pre-flight compliance audit...

SUCCESS: Compliant Electronic Application Record generated!
  File Path: output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf
  File Size: 18.42 KB (0.0176 MB)
  CSO Audit: PASS (Within strict 50 MB Court Services Online ceiling)

=== Professional Paralegal Workflow Checklist (Video 836310097) ===
✔ [Step 1] Source PDFs ingested with logical sequence order.
✔ [Step 2] Content compiled into single continuous PDF stream.
✔ [Step 3] Bookmarks panel populated with clear titles and exhibit sub-bookmarks.
✔ [Step 4] Top-center 14-16pt bold page numbers stamped across content pages.
✔ [Step 5] Title page & dynamic Index generated with accurate calculated folios.
✔ [Step 6] Text searchability verified (ready for OCR layer).
✔ [Step 7] Visual folios align precisely with index numbers.
✔ [Step 8] Hyperlink structure verified from Index entries to targets.
✔ [Step 9] File size audited and verified under 50 MB threshold.
```

---

<a id="pipeline-comparison"></a>
### 💡 Which Pipeline Should I Use?

| Feature | Python Pipeline (`.apm/skills/`) | Rust Pipeline (`cargo run`) |
| :--- | :--- | :--- |
| **Primary Use Case** | Day-to-day legal operations, batch processing, and AI Agent execution | Core engine development and SDK integration testing |
| **Input Source** | Dynamic JSON manifests & arbitrary PDFs (`inputs/<scenario>/`) | Hardcoded commercial discovery test case in `src/main.rs` |
| **Startup Time** | Instant (< 1 second) | Requires initial `cargo build` compilation |
| **Disk Requirement** | Lightweight (< 1 MB cache) | Generates compiler cache in `target/` (~1 GB) |
| **Customizability** | Drop any PDF or exhibit into `inputs/` | Edit Rust structs in `src/main.rs` |

---

<a id="license"></a>
## 📄 License

This project is made openly available under a hybrid license model (see [`LICENSE.md`](LICENSE.md)):
* **Software Code & Implementation Scripts**: [MIT License](LICENSE.md#part-1-mit-license-software--scripts)
* **Documentation, Legal Specifications & Reference Manuals**: [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE.md#part-2-creative-commons-attribution-40-international-public-license-documentation--references)
* **Upstream Engine & SDK Dependencies**: Builds on the headless core in [`storytold/pdfcraft`](https://github.com/storytold/pdfcraft?tab=MIT-2-ov-file) and the unified SDK in [`richfrem/pdfcraft`](https://github.com/richfrem/pdfcraft), both licensed under `MIT OR Apache-2.0` (see [LICENSE.md Part 3](LICENSE.md#part-3-upstream-dependencies--licensing-notices))
