# Repository Installation & Lifecycle Guide — bc-court-binder

This guide covers installing, configuring, deploying, and running the **BC Court Electronic Application Record (eBinder) Builder** and its unified agent skill (`managing-court-binders`).

It supports:
1. **APM Package Management (Recommended for AI Agents):** Deploying skills to Claude Code, GitHub Copilot, Codex, and Gemini / Antigravity via [APM](https://github.com/microsoft/apm).
2. **Standard Python Runtime (Zero-Compiler Setup):** Running the interactive terminal wizard, automated assembly, and 20-gate compliance validator directly with Python (`pypdf`, `pdfplumber`).
3. **Native Acceleration (Optional):** Pre-compiled PyO3 native wheels (`pdfcraft-pyo3`) for high-throughput batch processing.
4. **Rust Reference Implementation (Optional):** Compiling and executing the native in-process engine (`pdfcraft-sdk`).
5. **Desktop App (POC):** A native window with four screens (create sample filings, build a binder, check a binder, file with CSO) that reuses the same Python engine. Run it from source, or build a drag-to-Applications Mac installer (`.dmg`) that needs no Python. See [Option 4](#option-4-desktop-app).

---

## 📋 System Prerequisites

| Component | Minimum Version | Recommended | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | `3.9+` (`3.10+` for the desktop app) | `3.11`–`3.13` | Core agent skills, document assembly, and 20-gate validator |
| **pip** | `23.0+` | Latest | Dependency installation |
| **APM CLI** *(Optional)* | `0.33.0+` | `0.35.0+` | Installing the skill into AI agent environments |
| **Git** | `2.30+` | Latest | Cloning and revision management |
| **pywebview** *(Desktop app only)* | `5.3+` | Latest | Native window for the desktop app (`app/requirements-app.txt`) |
| **Rust / Cargo** *(Optional)* | `1.80+` | Latest Stable | Compiling the native `pdfcraft-sdk` reference engine (`src/main.rs`) |

---

## 📦 Option 1: APM Package Management (Recommended for AI Agents)

[Agent Package Manager (APM)](https://github.com/microsoft/apm) enables developers and legal-ops teams to install the `managing-court-binders` skill directly into any supported AI coding agent environment with a single command.

### 1. Install the APM CLI (if not already installed)

* **macOS / Linux:**
  ```bash
  curl -sSL https://aka.ms/apm-unix | sh -s -- @v0.35.0
  ```

* **Windows (PowerShell):**
  ```powershell
  irm https://aka.ms/apm-windows | iex
  ```

Verify APM installation:
```bash
apm --version
```

---

### 2. Install the Skill from GitHub into Your AI Agent Harness

To install the skill directly from the official GitHub repository into your agent environment:

#### A. Global Workstation Installation (Available in Any Folder)
Makes `managing-court-binders` available to your coding agents across your entire workstation:

```bash
# Target all installed agent environments (Claude, Copilot, Codex, Gemini/Antigravity):
apm install https://github.com/bcgov/bc-court-binder-builder --global --target claude,copilot,codex,gemini
```

> [!TIP]
> If using APM 0.35.0+, you can also specify `--target claude,copilot,codex,agy`.  
> Select multiple harnesses separated by commas. Repeating `--target` retains only the last value.

#### B. Project-Local Installation (For Specific Projects or Case Folders)
Installs the skill strictly within the current repository or legal case directory:

```bash
cd <path-to-case-or-repo>
apm install https://github.com/bcgov/bc-court-binder-builder --target claude,copilot,codex,gemini
```
This generates a local `apm.yml` and `apm.lock.yaml` recording the exact commit pin.

---

### 3. Target AI Agent Environments & Deployment Paths

APM automatically deploys the skill files to the correct configuration directories based on your `--target` selection:

| Target Flag | Target Agent Environment | Deployed Path (Global) | Deployed Path (Project Local) |
| :--- | :--- | :--- | :--- |
| `claude` | **Claude Code CLI** | `~/.claude/skills/managing-court-binders/` | `.claude/skills/managing-court-binders/` |
| `copilot` | **GitHub Copilot CLI** | `~/.agents/skills/managing-court-binders/` | `.agents/skills/managing-court-binders/` |
| `codex` | **OpenAI Codex CLI** | `~/.agents/skills/managing-court-binders/` | `.agents/skills/managing-court-binders/` |
| `gemini` / `agy` | **Gemini / Antigravity CLI** | `~/.gemini/antigravity-cli/skills/managing-court-binders/` | `.gemini/skills/` or shared `.agents/` |

---

### 4. Clone-Based Local APM Installation (For Developers & Maintainers)

If you have cloned the repository locally and want to link or deploy from your local working copy:

* **macOS / Linux:**
  ```bash
  git clone https://github.com/bcgov/bc-court-binder-builder.git
  cd bc-court-binder-builder
  apm install "$PWD/.apm/skills/managing-court-binders" --global --target claude,copilot,codex,gemini
  ```

* **Windows (PowerShell):**
  ```powershell
  git clone https://github.com/bcgov/bc-court-binder-builder.git
  cd bc-court-binder-builder
  apm install "$PWD\.apm\skills\managing-court-binders" --global --target claude,copilot,codex,gemini --parallel-downloads 0
  ```
  *(Note: `--parallel-downloads 0` prevents file-locking issues on Windows during staging directory moves).*

---

### 5. Managing & Auditing Installed APM Skills

```bash
# List all active skills installed via APM:
apm list

# Audit on-disk skill integrity:
apm audit

# Uninstall the skill globally:
apm uninstall https://github.com/bcgov/bc-court-binder-builder --global
```

---

### 6. 🤖 Complete Claude (Desktop & CLI) Walkthrough: From Scratch to Certified eBinder

This section assumes a completely fresh workstation with **zero pre-existing setup**. Do not assume steps have already been done. Follow this exact sequence:

```
┌─────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐
│  Phase 1: Install APM   │ ──> │  Phase 2: Install Skill│ ──> │  Phase 3: Open Claude  │
│  (CLI Toolchain)        │     │  (apm install --target)│     │  (Select Environment)  │
└─────────────────────────┘     └────────────────────────┘     └────────────────────────┘
                                                                            │
                                                                            ▼
┌─────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐
│  Phase 6: Real Filings  │ <── │  Phase 5: Test Loop    │ <── │  Phase 4: Auto-Setup   │
│  (Assemble & 20/20 PASS)│     │  (Closed-Loop Demo)    │     │  (/managing-court-... )│
└─────────────────────────┘     └────────────────────────┘     └────────────────────────┘
```

#### Phase 1: Verify or Install APM CLI (Terminal)
Open your terminal and verify whether APM is installed:
```bash
apm --version
```
If not installed, run:
* **macOS / Linux:**
  ```bash
  curl -sSL https://aka.ms/apm-unix | sh -s -- @v0.35.0
  ```
* **Windows (PowerShell):**
  ```powershell
  irm https://aka.ms/apm-windows | iex
  ```

#### Phase 2: Install the Skill into Claude via APM (Terminal)
Run the install command to deploy the skill into Claude:

* **Global Workstation Installation** *(Recommended — available across all your Claude sessions and projects)*:
  ```bash
  apm install https://github.com/bcgov/bc-court-binder-builder --global --target claude
  ```
* **Project-Local Installation** *(Scoped only to your current case or project folder)*:
  ```bash
  cd <path-to-case-folder>
  apm install https://github.com/bcgov/bc-court-binder-builder --target claude
  ```

Confirm installation:
```bash
apm list
# Output verifies: managing-court-binders -> .claude/skills/
```

#### Phase 3: Launch Claude & Select Workspace
* **Claude Desktop App:** Open Claude, click **`Choose environment ⌵`** in the center of the window, and choose your local machine environment pointing to your case folder (e.g. `bc-court-binder` or your legal case directory).
* **Claude Code CLI:** In your terminal, navigate to your case folder and type:
  ```bash
  claude
  ```

#### Phase 4: Run Agent-Guided Setup & Dependency Installation
In the Claude prompt bar, Claude automatically exposes the installed skill as a slash command. Type `/` and select `/managing-court-binders` (Claude renders it as a `[ /managing-court-binders ]` pill):

> **Prompt:**  
> `/managing-court-binders Check environment and set up dependencies for managing-court-binders.`

* **What Claude executes:** Claude runs the skill driver in `--mode setup`. It inspects Python 3.9+, verifies `pypdf` and `pdfplumber`, and automatically installs any missing dependencies via pip. No manual virtualenv troubleshooting is needed.

> [!TIP]
> **Conversational Zero-Parameter Invocation:**  
> If you simply type `/managing-court-binders` with no parameters (or say *"Help me create a court binder"*), Claude initiates an interactive conversation: asking whether you want to assemble files, audit an existing PDF, or run tests; requesting your folder path; confirming document sequence with you; and pre-flight validating the result.

#### Phase 5: Execute the Full Closed-Loop Verification Test
Once setup confirms all packages are installed, verify the deterministic pipeline with:

> **Prompt:**  
> `/managing-court-binders Run the complete court binder test loop.`

* **What Claude executes:** Claude runs `--mode all`, synthesizing authentic commercial discovery filings (Forms 32/33/35, affidavits, exhibits), assembling the continuous eBinder, and auditing against all 20 BC court rules.

#### Phase 6: Compile and Pre-Flight Validate Real Case Documents
To compile and certify actual court submissions:

> **Prompt:**  
> `/managing-court-binders Assemble a compliant BC Supreme Court application record from the files in ./inputs/01-commercial-discovery and pre-flight audit against the 20 court quality gates.`

* **What Claude delivers:**
  1. Compiles continuous two-pass folios starting at Tab 1 = Page 1.
  2. Generates Form 22 Style of Cause Title Page and 4-column Index.
  3. Injects invisible rectangle `/Border [0 0 0]` hyperlinks and stamps top-center $15\text{ pt}$ bold page numbers.
  4. Configures digital `/PageLabels` and hierarchical bookmarks.
  5. Displays the **20/20 PASS scorecard** certifying the record is ready for Court Services Online (CSO) submission.

---

### 7. 🧠 OpenAI Codex Walkthrough (Antigravity IDE & Codex CLI)

OpenAI Codex (`gpt-6-luna medium` / `codex`) operates natively with the `managing-court-binders` skill when loaded in Antigravity IDE or the Codex CLI.

#### Step 1: Deploy Skill for Codex
* **Global workstation deploy:**
  ```bash
  apm install ./.apm/skills/managing-court-binders --global --target codex
  ```
* **Project-local deploy** *(Recommended inside Codex sandboxes)*:
  ```bash
  apm install ./.apm/skills/managing-court-binders --target codex
  ```
  *(Writes to `.agents/skills/managing-court-binders/` which Codex automatically discovers).*

#### Step 2: Invoke via Codex Skill Prefix (`$`)
In Codex or Antigravity IDE's terminal prompt, skills are invoked using the `$` prefix:

> **Prompt:**  
> `$managing-court-binders Create a brand new set of 5 court filings from scratch in ./inputs/06-chambers-motion for an interim chambers application: 1. Form 32 Notice of Application 2. Form 33 Response 3. Form 35 Affidavit of Alex Morgan with Exhibit A and B 4. Form 35 Draft Order 5. RJR-MacDonald authority citation and principle summary. Then assemble into ./output/06-chambers-motion/Application_Record.pdf and validate against the 20 BC court rules.`

#### Step 3: Dynamic Document Synthesis & Manifest Bookmarks
When prompted to generate novel filings:
1. Codex authors synthetic text filing PDFs directly in `./inputs/<case-name>/`.
2. Codex compiles a companion `manifest.json`. To achieve a **100% 20/20 PASS (0 Hard Stops, 0 Soft Warnings)**, nested exhibits are declared under their parent affidavit with `rel_page` offsets:
   ```json
   {
     "tab": 3,
     "title": "Affidavit #1 of Alex Morgan",
     "filename": "03_Affidavit_Alex_Morgan.pdf",
     "exhibits": [
       { "name": "Exhibit A - Financial Ledger", "rel_page": 2 },
       { "name": "Exhibit B - Email Correspondence", "rel_page": 3 }
     ]
   }
   ```
3. Codex runs the assembler and validator, rendering the complete statutory audit table certifying full compliance.

> [!NOTE]
> **Subprocess Sandbox Invariant:**  
> Codex CLI isolates subprocess file writes strictly to the active workspace. If performing global APM operations (`apm install --global`), execute them on the host terminal rather than inside a sandboxed Codex subshell.

---

### 8. 🐙 GitHub Copilot Integration Guide (Desktop App, CLI, & VS Code)

GitHub Copilot supports the Agent Skills specification (`SKILL.md`) natively through multiple interfaces.

#### Crucial Distinction: Microsoft Copilot vs. GitHub Copilot
Ensure you are using the developer-oriented **GitHub Copilot** tooling:
* ❌ **Microsoft Copilot macOS App** (`/Applications/Copilot.app`, bundle `com.microsoft.m365copilot`): Consumer/Enterprise M365 AI chat (Bing/Office). It operates in an isolated web sandbox without access to local workspace files, terminal processes, or APM agent skills.
* ✅ **GitHub Copilot Desktop App** (`/Applications/GitHub Copilot.app`, bundle `com.github.githubapp`): Dedicated GitHub developer desktop assistant.
* ✅ **GitHub Copilot CLI** (`copilot` / `gh copilot`): Command-line coding agent with native Agent Skills support.
* ✅ **VS Code / Antigravity IDE Extension**: GitHub Copilot Chat extension configured with `.github/copilot-instructions.md`.

#### Step 1: Verify Skill Discovery in Copilot
GitHub Copilot automatically searches `.agents/skills/`, `.claude/skills/`, and `~/.agents/skills/`. Verify that `managing-court-binders` is detected:
```bash
cd ~/Projects/bc-court-binder
copilot skill list
```
The output confirms discovery under **Project skills**:
```text
Project skills:
  managing-court-binders - Compiles, stamps, bookmarks, and audits BC Supreme Court and Court of Appeal electronic application records and books of authorities. Use when generating synthetic filings, assembling court binders, or auditing against PD-72 and CSO compliance gates.
```

#### Step 2: Launch GitHub Copilot Desktop App Scoped to Workspace
To open the standalone GitHub Copilot desktop application pre-scoped to your court binder workspace:
```bash
cd ~/Projects/bc-court-binder
copilot app
```
The desktop app opens with the repository, files, and skill instructions immediately available in context.

#### Step 3: Interactive Copilot CLI Execution
To run an interactive session in your terminal:
```bash
cd ~/Projects/bc-court-binder
copilot
```
Simply prompt Copilot conversationally:
> *"Assemble a compliant BC Supreme Court application record from ./inputs/01-commercial-discovery and run the pre-flight validation audit."*

Copilot invokes the pipeline scripts, calculates two-pass folios, builds the Form 22 Title Page and Index, and outputs the 20-gate scorecard.

#### Step 4: Non-Interactive Headless Scripting (CI/CD / Automation)
For unattended batch runs or automated pre-flight gates:
```bash
copilot -C ~/Projects/bc-court-binder -p "Run the complete court binder test loop" --allow-all-tools
```

#### Step 5: Dynamic Custom Motion Synthesis (Verified 20/20 PASS)
In the GitHub Copilot Mac Desktop App, prompt Copilot to synthesize a novel chambers application:

> **Prompt:**  
> `/managing-court-binders Create a brand new set of 5 court filings from scratch in ./inputs/07-copilot-production-motion for a Rule 7-1(18) Application for Document Production: 1. Form 32 Notice of Application 2. Form 33 Application Response 3. Form 35 Affidavit of Sarah Chen, CPA, with Exhibit A and B 4. Form 35 Draft Order 5. Case Authority Summary citing British Columbia v. Imperial Tobacco Canada Ltd., 2004 SCC 50. Declare Exhibit A at rel_page: 2 and Exhibit B at rel_page: 3 under the affidavit in manifest.json, assemble into ./output/07-copilot-production-motion/Application_Record.pdf, and pre-flight validate against all 20 BC court rules.`

* **Verified Output:**
  * **Assembled Binder:** `output/07-copilot-production-motion/Application_Record.pdf` (17 pages, 17 bookmarks, 7 index hyperlinks, 30,244 bytes).
  * **Scorecard Result:** **20/20 PASSED — 0 Hard Stops, 0 Soft Warnings (100% Compliant & Approved for CSO Submission)**.
  * **Archived Evidence:** Visual verification screenshots archived under `docs/assets/screenshots/copilot/`.

---

## 🐍 Option 2: Python Environment & Direct Execution (Zero Compiler Setup)

If you prefer to run the scripts directly without APM, the entire pipeline operates out of the box using pure Python with zero C/C++ or Rust compiler requirements.

### Step 1: Clone Repository
```bash
git clone https://github.com/bcgov/bc-court-binder-builder.git
cd bc-court-binder-builder
```

### Step 2: Set Up Virtual Environment
* **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
  *(If script execution is restricted: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> [!NOTE]
> `requirements.txt` contains only `pypdf` and `pdfplumber` (the desktop app adds `pywebview` through `app/requirements-app.txt`). This lightweight footprint provides 100% of the functionality needed to synthesize filings, assemble binders, stamp folios, inject GoTo links, and execute the 20-gate compliance audit.

### Step 4 (Optional): The PdfCraft native wheel
The PdfCraft Python package is a thin Python layer over the compiled Rust engine (`pdfcraft._native`). You can install the pre-built wheel from GitHub Releases:
```bash
# macOS Apple Silicon, Python 3.13 only (the wheel's tag is cp313-cp313-macosx_11_0_arm64):
pip install "https://github.com/richfrem/pdfcraft/releases/download/v0.16.1/pdfcraft-0.5.0-cp313-cp313-macosx_11_0_arm64.whl"
```
The wheel only copies files into `site-packages` (no install scripts) and pulls in `pypdf` and `pillow`. Its SHA-256 is `53f52d2f154d723c50836c2820f9ce19fb4bc9f0c2bd88c48f1b8e3b2a364f46`.

> [!NOTE]
> **The binder engine does not call PdfCraft yet.** Today the generator and assembler write the cover, index and bookmarks themselves and use `pypdf` to copy in the original PDF pages, and the validator reads them with `pypdf`, so installing the wheel changes nothing about the output, and every compliance check works without it. The [Mac installer](#mac-app) still bundles the wheel so the native engine is ready when the engine starts to use it (for example, to merge original PDFs as true copies).

---

## 🎮 Running the Interactive Skill

Once installed or cloned, you can run the skill in multiple ways:

### 1. Guided Interactive Terminal Wizard (Recommended for Human Operators)
```bash
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --interactive
```
The wizard guides you through:
1. **Selecting Workflow:** Assemble Binder, Validate PDF, Synthesize Test Filings, or Complete Pipeline.
2. **Selecting Matter Type:** Commercial Discovery (Rule 7-1), Notice of Application Amendment (Rule 8-1), or Family Law.
3. **Input & Output Configuration:** Choosing source document directories and target PDF path.
4. **Execution & Scorecard:** Live progress reporting and statutory 20-gate compliance scorecard.

---

### 2. Headless Operational Modes (For Automation & CI/CD)

```bash
# A. Complete Closed-Loop Demonstration (Generates inputs -> Assembles -> Validates)
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode all

# B. Assemble an Electronic Application Record from an input directory
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode assemble \
  --inputs inputs/01-commercial-discovery \
  --output output/01-commercial-discovery/Application_Record.pdf

# C. Pre-flight Audit a Candidate PDF against the 20 Court Quality Gates
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode validate \
  --output output/01-commercial-discovery/Application_Record.pdf

# D. Synthesize authentic chambers filings with manifest.json
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode generate \
  --inputs inputs/01-commercial-discovery \
  --matter-type discovery

# E. Run environment diagnostics and dependency checks
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode setup
```

---

### 3. Natural Language Prompts for AI Agents (Claude, Copilot, Codex, Antigravity)

Once deployed via APM, your AI agents will automatically recognize prompts such as:
* *"Build a compliant BC Supreme Court application record from the PDFs in `./inputs/01-commercial-discovery`."*
* *"Validate `./output/Application_Record.pdf` against the 20 statutory quality gates and show the compliance scorecard."*
* *"Synthesize a set of authentic chambers filings for an amendment application under Rule 8-1."*
* *"Check whether this court binder satisfies Practice Direction 72 and Court Services Online requirements."*

---

## 🦀 Option 3: Optional Rust Reference Pipeline (`pdfcraft-sdk`)

For developers working directly on low-level PDF engine primitives or embedding the Rust Layer 7 SDK:

### 1. Install Rust & Cargo (if not installed)
* **macOS / Linux:**
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  source "$HOME/.cargo/env"
  ```
* **Windows (PowerShell):**
  ```powershell
  winget install --id Rustlang.Rustup
  ```
Verify: `rustc --version` (Requires `1.80+`).

### 2. Execute Native Reference Engine
```bash
cargo run
```
This builds and executes [`src/main.rs`](src/main.rs), which compiles an in-memory commercial discovery record, calls `pdfcraft-sdk` Layer 7 client for raster engine verification, and outputs:
```text
output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf
```

---

<a id="option-4-desktop-app"></a>
## 🖥️ Option 4: Desktop App (POC)

The desktop app is an alternative to chatting with an agent. It calls the same `managing-court-binders` scripts, so results match the skill exactly. Everything runs locally. It needs this repository checkout (the app finds the skill at `.apm/skills/managing-court-binders/scripts/`).

<a id="mac-app"></a>
### 📦 Install the Mac app (no Python needed)

A Mac disk image (`.dmg`) bundles the app, the skill scripts, Python, `pypdf` and the PdfCraft native engine, so users only drag the app to **Applications**. A downloadable release is not published yet, so build it once on a Mac:

```bash
git clone https://github.com/bcgov/bc-court-binder-builder.git
cd bc-court-binder-builder
packaging/macos/build_dmg.sh
```

The script creates its own build environment (`packaging/macos/.venv-build`, nothing is installed into `app/.venv`), downloads the PdfCraft wheel from the release URL in [Step 4](#step-4-optional-the-pdfcraft-native-wheel) and refuses to continue unless its SHA-256 matches the pinned hash. That is the build-time equivalent of the `pip install` above, so users never run `pip`. It then builds the app and runs a self-test on the packaged app: a sample binder must pass all 20 gates and the native PdfCraft engine must merge two PDFs, otherwise the build fails. The image is written to `packaging/macos/dist/Court-binder-builder-<version>-macos-<arch>.dmg` (about 40 MB).

**Install:** open the `.dmg`, drag **Court binder builder** onto **Applications**, then open it from Applications or Launchpad.

**Things to know**
- **Unsigned.** On the Mac that built it, the app opens normally. A copy downloaded from the internet triggers a Gatekeeper warning: right-click the app, choose **Open**, then **Open** again (or run `xattr -dr com.apple.quarantine "/Applications/Court binder builder.app"`). Signed and notarized builds need an Apple Developer ID; see [`packaging/macos/README.md`](packaging/macos/README.md) (untested here).
- **One architecture and one Python per build.** A build made on Apple Silicon (`arm64`) does not run on Intel Macs, and the other way round. The pinned PdfCraft wheel is for Python 3.13 on Apple Silicon only; set `PDFCRAFT_WHEEL` to another wheel, or `WITH_PDFCRAFT=0` to build without it.
- **Folders.** An installed app saves to `~/Documents/BC Court Binder` (sample filings) and `~/Documents/BC Court Binder/Output` (binders) until you change them in the sidebar. Choices are kept in `~/.bc_court_binder_settings.json`, shared with a copy run from source on the same Mac.
- A **Windows installer** is planned and not built yet.

### 🐍 Run from source

**Requirements:** Python **3.10 or newer** (3.11–3.13 recommended), Git, and the dependencies in [`app/requirements-app.txt`](app/requirements-app.txt) (`pywebview`, plus `pypdf` and `pdfplumber` from the root [`requirements.txt`](requirements.txt)). No compiler is needed.

### 🍎 macOS

1. **Check for Python 3.10+:** `python3 --version`. If it is older or missing, install one:
   * Download the macOS installer from [python.org/downloads](https://www.python.org/downloads/), or
   * `brew install python@3.12` (with [Homebrew](https://brew.sh)).
2. **Get the code, create an environment, install, launch:**
   ```bash
   git clone https://github.com/bcgov/bc-court-binder-builder.git
   cd bc-court-binder-builder
   python3 -m venv app/.venv
   source app/.venv/bin/activate
   pip install --upgrade pip
   pip install -r app/requirements-app.txt
   cd app && python -m binder_app.main
   ```
3. The window uses the system WebKit view, so nothing else is required.

### 🪟 Windows 10 / 11

1. **Install Python 3.10+** from [python.org/downloads](https://www.python.org/downloads/windows/) (tick **Add python.exe to PATH**), or in PowerShell: `winget install Python.Python.3.12`. Open a **new** terminal, then check: `py --version`.
2. **Make sure the WebView2 runtime is installed.** It is preinstalled on Windows 11 and current Windows 10. If the window opens blank or fails to start: `winget install Microsoft.EdgeWebView2Runtime`.
3. **Get the code, create an environment, install, launch (PowerShell):**
   ```powershell
   git clone https://github.com/bcgov/bc-court-binder-builder.git
   cd bc-court-binder-builder
   py -m venv app\.venv
   app\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r app\requirements-app.txt
   cd app
   python -m binder_app.main
   ```
   * If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
   * In Command Prompt use `app\.venv\Scripts\activate.bat`.
   * Deep clone paths can fail on Windows; clone to a short path such as `C:\src\bc-court-binder` (see [Windows Path Limits](#windows-path-limits--execution-policies)).

### 🐧 Linux (untested)

Install GTK and WebKit first, for example on Debian or Ubuntu: `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1`, then `pip install "pywebview[gtk]"` in addition to the steps above.

### Using it

1. **Working folder and Output folder** (sidebar): the working folder (default `inputs/` in the repo) is where sample filings are created; the output folder (default `output/`) is where finished binders go. **Change…** remembers your choice in `~/.bc_court_binder_settings.json`.
2. **Create sample filings → Run full test cycle:** writes the filings to `Sample run <timestamp>/filings/` in the working folder and the binder to `Sample run <timestamp>/Application_Record_Sample.pdf` in the output folder, then shows the scorecard (expect 20 / 20).
3. **Build a binder:** choose a folder of filings. Optionally open **Title page details** (court file number, registry, parties, hearing date, time estimate, counsel). They print on the binder's own title page, are saved as `manifest.json` in the filings folder and are prefilled next time. Anything left blank is marked as a placeholder, and the result tells you what to complete before filing. If your folder contains `000_Application_Record_Title_Page.txt`, that is used as the title page instead. Your original PDF pages are used unchanged (true copies); a filing with no PDF is typeset from its text and flagged. Check the suggested file name and press **Build binder**. The PDF is saved in the folder shown under **Save binder in** (by default a subfolder of the output folder named after your filings folder; use **Choose folder…** to pick another). Existing files are never overwritten. **Check this binder** jumps to step 3.
4. **Check a binder:** choose any PDF to audit it.
5. **File with CSO:** answer three questions (CSO account? logged on? card registered?) and use the buttons to open the right CSO page in your browser. Choose a binder to see whether it can be uploaded directly (up to 20 MB), needs **Upload Large Files** first (20 to 50 MB) or is too large. You log on, add your card and submit yourself; nothing you type on CSO passes through the app.

**Verify the engine without opening the window** (from the `app` folder, environment active):
```bash
python -m unittest discover -s tests -t .
```

### Desktop app troubleshooting

| Symptom | Fix |
| :--- | :--- |
| `needs Python 3.10 or newer` | Install a newer Python (steps above) and recreate `app/.venv` with it. |
| `ModuleNotFoundError: No module named 'webview'` | The environment is not active or dependencies are missing: activate `app/.venv`, then `pip install -r app/requirements-app.txt`. |
| `ModuleNotFoundError: No module named 'binder_app'` | Run from inside the `app` folder: `cd app && python -m binder_app.main`. |
| Blank window on Windows | Install the WebView2 runtime (see above). |
| `Could not find the managing-court-binders scripts` | Run from a full clone, or set `BC_BINDER_SCRIPTS` to the skill's `scripts` folder. |

To avoid installing Python at all on a Mac, build the [Mac installer](#mac-app) from [`packaging/macos/`](packaging/macos/README.md). A Windows installer is planned and not built yet.

---

## 🛠️ Platform Specifics & Troubleshooting

### Windows Path Limits & Execution Policies
1. **PowerShell Script Execution:**
   If activating `.venv` gives an execution policy error:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```
2. **Windows Path Length Limitations:**
   If installing from deep Git paths triggers `[WinError 3] The system cannot find the path specified`:
   * Enable long paths in PowerShell (Administrator):
     ```powershell
     New-ItemProperty -Path HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem -Name LongPathsEnabled -Value 1 -PropertyType DWORD -Force
     git config --global core.longpaths true
     ```
   * Or install from a short local clone path (e.g. `C:\src\bc-court-binder`).

### macOS & Linux Permissions
Ensure script execution permissions are enabled:
```bash
chmod +x .apm/skills/managing-court-binders/scripts/*.py
```

### Module Not Found Errors
If `ModuleNotFoundError: No module named 'pypdf'` occurs, verify that your virtual environment is active:
```bash
which python3   # Should point to <repo>/.venv/bin/python3
pip list        # Should list pypdf and pdfplumber
```
