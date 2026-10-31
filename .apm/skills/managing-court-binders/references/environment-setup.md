# Environment Setup & Requirements Verification

This guide explains how to verify and configure the runtime environment for `bc-court-binder` across macOS, Windows, and Linux.

## Contents

- [Prerequisites Overview](#prerequisites-overview)
- [Python Virtual Environment Setup](#python-virtual-environment-setup)
- [Installing Python Requirements](#installing-python-requirements)
- [Optional Native PdfCraft Acceleration Wheel](#optional-native-pdfcraft-acceleration-wheel)
- [Optional Rust Toolchain Setup](#optional-rust-toolchain-setup)
- [Automated Environment Verification](#automated-environment-verification)

---

## Prerequisites Overview

| Component | Minimum Version | Required For |
| :--- | :--- | :--- |
| **Python** | `3.9+` (Recommended `3.11`–`3.13`) | Core binder generation, assembly, and 20 quality gates |
| **pip** | `23.0+` | Installing python packages and native wheels |
| **pypdf** | `5.0+` | PDF container parsing, folio math, and annotation generation |
| **pdfplumber** | `0.11+` | Spatial bounding box margin auditing and Shannon character entropy |
| **pdfcraft (native)** *(Optional)* | `0.5.0+` | In-process native Rust engine acceleration |
| **Rust / Cargo** *(Optional)* | `1.80+` | Executing the native Rust engine POC (`src/main.rs`) |

---

## Python Virtual Environment Setup

Always use an isolated virtual environment:

### macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

---

## Installing Python Requirements

Install the mandatory dependencies for the skill pipeline:

```bash
pip install -r requirements.txt
```

This installs `pypdf` and `pdfplumber`, which provide 100% of the functionality needed to assemble and validate court binders.

---

## Optional Native PdfCraft Acceleration Wheel

To install the native PyO3 acceleration module pre-compiled from GitHub Releases:

```bash
# macOS (Apple Silicon arm64):
pip install "https://github.com/richfrem/pdfcraft/releases/download/v0.16.1/pdfcraft-0.5.0-cp313-cp313-macosx_11_0_arm64.whl"

# Or from local source if developing beside pdfcraft:
pip install ../pdfcraft/sdks/python
```

*(If not installed, the pipeline operates with zero degradation using built-in vector serialization).*

---

## Optional Rust Toolchain Setup

If you want to run or test the native Rust reference engine (`src/main.rs`):

* **macOS / Linux:**
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  source "$HOME/.cargo/env"
  ```
* **Windows:**
  ```powershell
  winget install --id Rustlang.Rustup
  ```

---

## Automated Environment Verification

To verify that all requirements are properly installed, run the skill in `setup` mode:

```bash
python3 .apm/skills/managing-court-binders/scripts/managing_court_binders.py --mode setup
```
