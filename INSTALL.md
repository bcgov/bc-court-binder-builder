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

# Install requirements (pypdf, pdfplumber)
pip install -r requirements.txt
```

> [!NOTE]
> `pip install -r requirements.txt` is **all that is required** to run the unified skill (`managing-court-binders`), assemble binders, stamp folios, inject hyperlinks, and validate against the 20 court quality gates.
> 
> **Optional: Native PdfCraft SDK Acceleration (PyO3 Engine):**
> Install the pre-built native wheel directly from GitHub Releases:
> ```bash
> pip install "https://github.com/richfrem/pdfcraft/releases/download/v0.16.1/pdfcraft-0.5.0-cp313-cp313-macosx_11_0_arm64.whl"
> ```
> *(Or from local source if developing side-by-side: `pip install ../pdfcraft/sdks/python`). If no native wheel is installed, the pipeline operates 100% out of the box using built-in vector serialization.*

### Step 4: Verify Installation & Run Skill Right Away

Every fresh clone can immediately run the unified `managing-court-binders` skill out of the box:

```bash
# Option A: Run the complete closed-loop lifecycle in one command
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode all

# Option B: Run individual steps as needed
# 1. Generate a fresh set of input filings (discovery | amendment | family)
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode generate \
  --inputs inputs/01-commercial-discovery \
  --matter-type discovery

# 2. Assemble the input documents into a compliant court binder
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode assemble \
  --inputs inputs/01-commercial-discovery \
  --output output/01-commercial-discovery/Application_Record.pdf

# 3. Audit against the 20 statutory BC Court quality gates
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py \
  --mode validate \
  --output output/01-commercial-discovery/Application_Record.pdf
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

> [!NOTE]
> `pip install -r requirements.txt` provides everything required to run the unified skill out of the box. Installing the native PyO3 acceleration module (`pdfcraft-pyo3`) is optional. If developing alongside a local `pdfcraft` clone, run `pip install ..\pdfcraft\sdks\python`.

### Step 4: Verify Installation
```powershell
python .apm\skills\managing-court-binders\scripts\managing_court_binders.py --mode all
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

# Run full end-to-end assembly and pre-flight validation
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode all
```

---

## 🦀 4. Optional: Rust SDK Runner Setup

If you wish to compile and run the native Rust example ([`src/main.rs`](src/main.rs)) to verify direct `pdfcraft-sdk` integration:

### 4.1 Install the Rust Toolchain (if not already installed)
To install the official Rust compiler (`rustc`) and package manager (`cargo`):

* **macOS / Linux:**
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  source "$HOME/.cargo/env"
  ```
* **Windows (PowerShell):**
  ```powershell
  # Via winget:
  winget install --id Rustlang.Rustup
  # Or download and run rustup-init.exe from https://rustup.rs
  ```

Verify your installation:
```bash
rustc --version   # Requires 1.80+
cargo --version
```

### 4.2 Dependencies in `Cargo.toml`:
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

### What `cargo run` Does:
1. Compiles `src/main.rs` against `pdfcraft-sdk`.
2. Synthesizes an in-memory commercial discovery case (5 items: Notice of Application, Response, Eleanor Vance Affidavit with Exhibits A & B, Draft Order, and Legal Authority).
3. Calculates dynamic page folios, generates the Title Page and Index with invisible rectangle link annotations, stamps top-center $15\text{ pt}$ bold folios, and configures `/PageLabels` and Initial View outlines.
4. Uses `pdfcraft_sdk::LocalClient::render_page()` to run raster engine verification on Page 1.
5. Audits against the 50 MB CSO limit and saves the compiled PDF to:
   ```text
   output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf
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
