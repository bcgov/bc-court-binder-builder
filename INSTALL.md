# Installation & Setup Guide: bc-court-binder

This guide covers installing and configuring `bc-court-binder` across macOS, Windows, and Linux environments.

---

## 📋 Prerequisites

| Runtime | Minimum Version | Required For |
| :--- | :--- | :--- |
| **Python** | `3.9+` (Recommended: `3.11`–`3.13`) | Core Agent Skills, automated assembly, and 20-gate validator |
| **pip** | `23.0+` | Package and native `.whl` installation |
| **Git** | `2.30+` | Cloning and version control |
| **Rust / Cargo** *(Optional)* | `1.80+` | Only needed if executing or modifying the native Rust SDK example |

---

## 🍎 1. macOS Installation (Apple Silicon & Intel)

### Step 1: Clone Repository
```bash
git clone https://github.com/richfrem/bc-court-binder.git
cd bc-court-binder
```

### Step 2: Set Up Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

#### Installing the Native PdfCraft SDK Wheel:
To install the pre-compiled native PyO3 engine wheel for macOS (Apple Silicon):
```bash
pip install "https://github.com/richfrem/pdfcraft/releases/download/v0.16.1/pdfcraft-0.5.0-cp313-cp313-macosx_11_0_arm64.whl"
```
*(If building on an Intel Mac or without pre-compiled wheels, the pipeline automatically falls back to pure-Python vector serialization).*

### Step 4: Verify Installation & Run Skills Right Away

Every fresh clone can immediately run the 3 skills out of the box:

```bash
# Skill 1: Generate a fresh set of input filings (discovery | amendment | family)
python3 .apm/skills/generating-court-documents/scripts/generating_court_documents.py \
  --output-dir inputs/01-commercial-discovery \
  --matter-type discovery

# Skill 2: Assemble the input documents into a compliant court binder
python3 .apm/skills/assembling-court-binders/scripts/assembling_court_binders.py \
  --inputs inputs/01-commercial-discovery \
  --output output/01-commercial-discovery/Application_Record.pdf

# Skill 3: Audit against the 20 statutory BC Court quality gates
python3 .apm/skills/validating-court-binders/scripts/validating_court_binders.py \
  --file output/01-commercial-discovery/Application_Record.pdf
```
Expected output:
```text
SUMMARY SCORECARD:
  - Hard Stops (Fatal Court Rejections): 0
  - Soft Warnings (Formatting Advisories): 0
  - Passed Rules:                        20 / 20
FINAL VERDICT: 100% COMPLIANT - ALL GATES PASSED (APPROVED FOR CSO SUBMISSION)
```

---

## 🪟 2. Windows Installation (PowerShell)

### Step 1: Clone Repository
In PowerShell:
```powershell
git clone https://github.com/richfrem/bc-court-binder.git
cd bc-court-binder
```

### Step 2: Set Up Python Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 3: Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Installing the Native PdfCraft SDK Wheel for Windows:
```powershell
pip install "https://github.com/richfrem/pdfcraft/releases/download/v0.16.1/pdfcraft-0.5.0-cp313-cp313-win_amd64.whl"
```

### Step 4: Verify Installation
```powershell
python .apm\skills\assembling-court-binders\scripts\assembling_court_binders.py `
  --inputs inputs\01-commercial-discovery `
  --output output\01-commercial-discovery\Application_Record.pdf

python .apm\skills\validating-court-binders\scripts\validating_court_binders.py `
  --file output\01-commercial-discovery\Application_Record.pdf
```

---

## 🐧 3. Linux Installation (Ubuntu / Debian / RHEL)

```bash
git clone https://github.com/richfrem/bc-court-binder.git
cd bc-court-binder

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Run assembly and pre-flight validation
python3 .apm/skills/assembling-court-binders/scripts/assembling_court_binders.py \
  --inputs inputs/01-commercial-discovery \
  --output output/01-commercial-discovery/Application_Record.pdf
```

---

## 🦀 4. Optional: Rust SDK Runner Setup

If you wish to compile and run the native Rust example (`src/main.rs`):

### Dependencies in `Cargo.toml`:
```toml
[dependencies]
pdfcraft-sdk = { git = "https://github.com/richfrem/pdfcraft", branch = "main" }
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }

# Optional local override when developing side-by-side with pdfcraft checkout:
[patch."https://github.com/richfrem/pdfcraft"]
pdfcraft-sdk = { path = "../pdfcraft/crates/sdk" }
```

### Execution:
```bash
cargo run
```

---

## 🛠️ Troubleshooting

### 1. `ModuleNotFoundError: No module named 'pypdf'`
Ensure your virtual environment is active (`source .venv/bin/activate` or `.venv\Scripts\Activate.ps1`), then re-run:
```bash
pip install -r requirements.txt
```

### 2. Disk Space Caution during Rust Builds
Rust debug builds can consume several gigabytes of disk in `target/`. If you are low on disk space, stick to the **Python Skills pipeline**, which runs with zero compilation cache and negligible disk impact (< 1 MB).

### 3. File Permissions on macOS / Linux
Ensure script permissions are executable:
```bash
chmod +x .apm/skills/*/scripts/*.py
```
