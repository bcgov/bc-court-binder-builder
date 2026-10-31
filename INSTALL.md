# Repository Installation & Lifecycle Guide — bc-court-binder

This guide covers installing, configuring, deploying, and running the **BC Court Electronic Application Record (eBinder) Builder** and its unified agent skill (`managing-court-binders`).

It supports:
1. **APM Package Management (Recommended for AI Agents):** Deploying skills to Claude Code, GitHub Copilot, Codex, and Gemini / Antigravity via [APM](https://github.com/microsoft/apm).
2. **Standard Python Runtime (Zero-Compiler Setup):** Running the interactive terminal wizard, automated assembly, and 20-gate compliance validator directly with Python (`pypdf`, `pdfplumber`).
3. **Native Acceleration (Optional):** Pre-compiled PyO3 native wheels (`pdfcraft-pyo3`) for high-throughput batch processing.
4. **Rust Reference Implementation (Optional):** Compiling and executing the native in-process engine (`pdfcraft-sdk`).

---

## 📋 System Prerequisites

| Component | Minimum Version | Recommended | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | `3.9+` | `3.11`–`3.13` | Core agent skills, document assembly, and 20-gate validator |
| **pip** | `23.0+` | Latest | Dependency installation |
| **APM CLI** *(Optional)* | `0.33.0+` | `0.35.0+` | Installing the skill into AI agent environments |
| **Git** | `2.30+` | Latest | Cloning and revision management |
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

### 6. 🤖 Claude Code Walkthrough: From APM Install to First Court Binder

If you are using **Claude Code**, follow this 3-step walkthrough to get up and running:

#### Step 1: Install the Skill with APM
Run this once from your terminal to make the skill available across all your Claude Code sessions:
```bash
apm install https://github.com/bcgov/bc-court-binder-builder --global --target claude
```
APM automatically provisions the complete skill into `~/.claude/skills/managing-court-binders/`.

#### Step 2: Open Claude Code
In your project directory or case folder:
```bash
claude
```
Claude Code automatically discovers `managing-court-binders` from `~/.claude/skills/`.

#### Step 3: Let Claude Guide Your Setup & Execution
You don't need to manually configure virtual environments or debug missing packages. Claude Code handles the lifecycle through conversational prompts:

1. **Assisted Dependency Check & Setup:**
   > **You:** *"Check environment and set up dependencies for managing-court-binders."*  
   > **Claude:** Runs `--mode setup`, validates Python 3.9+, verifies `pypdf` and `pdfplumber`, and installs any missing packages via pip automatically.

2. **Run End-to-End Test Loop:**
   > **You:** *"Run the complete court binder test loop."*  
   > **Claude:** Runs `--mode all`, generating authentic multi-page commercial discovery filings (Forms 32/33/35, affidavits, exhibits), assembling the hyperlinked eBinder, and auditing against all 20 BC court quality gates.

3. **Assemble Your Case Files:**
   > **You:** *"Assemble a compliant BC Supreme Court application record from the PDFs in `./inputs/my-case`."*  
   > **Claude:** Scans the folder, orders the filings, generates the Form 22 Style of Cause Title Page and 4-column Index, stamps top-center folios, configures `/PageLabels`, injects `/Border [0 0 0]` invisible links, and builds hierarchical bookmarks.

4. **Statutory 20-Gate Pre-Flight Audit:**
   > **You:** *"Validate `./output/Application_Record.pdf` against the 20 court quality gates and give me the scorecard."*  
   > **Claude:** Executes the pre-flight audit and displays the pass/fail scorecard before you submit to Court Services Online.

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
> `requirements.txt` contains only `pypdf` and `pdfplumber`. This lightweight footprint provides 100% of the functionality needed to synthesize filings, assemble binders, stamp folios, inject GoTo links, and execute the 20-gate compliance audit.

### Step 4 (Optional): High-Performance Native PyO3 Wheel Acceleration
To enable native Rust acceleration via PyO3 without compiling from source, install the pre-built wheel from GitHub Releases:
```bash
# macOS Apple Silicon (ARM64):
pip install "https://github.com/richfrem/pdfcraft/releases/download/v0.16.1/pdfcraft-0.5.0-cp313-cp313-macosx_11_0_arm64.whl"
```
*(If no native wheel is installed, the pipeline automatically falls back to standard Python vector serialization with zero degradation in compliance).*

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
