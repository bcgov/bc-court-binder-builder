#!/usr/bin/env python3
"""
managing_court_binders.py
=========================
PURPOSE:
    Unified CLI driver and terminal wizard for the BC Supreme Court Electronic Application
    Record & Book of Authorities lifecycle. Orchestrates environment verification,
    synthetic filing drafting, two-pass binder assembly, and 20-gate statutory auditing.

KEY INPUT DEPENDENCIES:
    - inputs/<matter>/manifest.json     : Document sequence and metadata
    - inputs/<matter>/*.pdf or *.txt    : Source court pleadings and exhibit documents
    - requirements.txt                  : pypdf>=5.0.0, pdfplumber>=0.11.0

FUNCTION INDEX:
    - check_or_setup_environment(auto_install: bool = False) -> bool
    - display_menu() -> None
    - prompt_choice() -> str
    - interactive_menu() -> tuple[str, str, str, str, bool]
    - main() -> None

USAGE:
    python3 managing_court_binders.py --mode assemble --inputs inputs/01-commercial-discovery --output output/01-commercial-discovery/Application_Record.pdf
    python3 managing_court_binders.py --mode validate --output output/01-commercial-discovery/Application_Record.pdf
    python3 managing_court_binders.py --mode setup
    python3 managing_court_binders.py --interactive
"""

import sys
import argparse
from pathlib import Path

# Module-level default path constants
DEFAULT_INPUTS_DIR = "inputs/01-commercial-discovery"
DEFAULT_OUTPUT_PDF = "output/01-commercial-discovery/Application_Record.pdf"

# Add current script directory to path to import sibling scripts
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import generating_court_documents
    import assembling_court_binders
    import validating_court_binders
except ImportError as e:
    # Fallback if imported from outside
    pass

def check_or_setup_environment(auto_install: bool = False) -> bool:
    """Verifies that all runtime requirements are satisfied, with auto-installation option."""
    print("================================================================================")
    print("       CHECKING RUNTIME ENVIRONMENT & DEPENDENCIES FOR BC-COURT-BINDER          ")
    print("================================================================================\n")
    
    # 1. Check Python
    py_ver = sys.version_info
    print(f"✔ Python: {py_ver.major}.{py_ver.minor}.{py_ver.micro} (Requires 3.9+)")
    
    missing_required = []
    
    # 2. Check pypdf
    try:
        import pypdf
        print(f"✔ pypdf: {getattr(pypdf, '__version__', 'installed')} (Required: PDF container, folios, links)")
    except ImportError:
        print("✖ pypdf: NOT INSTALLED (Required for PDF assembly and folio math)")
        missing_required.append("pypdf>=5.0.0")

    # 3. Check pdfplumber
    try:
        import pdfplumber
        print(f"✔ pdfplumber: {getattr(pdfplumber, '__version__', 'installed')} (Required: spatial & entropy audit)")
    except ImportError:
        print("✖ pdfplumber: NOT INSTALLED (Required for 20-gate compliance audit)")
        missing_required.append("pdfplumber>=0.11.0")

    # 4. Check native pdfcraft (Optional)
    try:
        import pdfcraft
        print(f"✔ pdfcraft (native PyO3): {getattr(pdfcraft, '__version__', '0.5.0')} (Optional: high-speed engine acceleration)")
    except ImportError:
        print("ℹ pdfcraft (native PyO3): Not installed (Optional; pure-Python vector fallback is active)")

    # 5. Check Rust / Cargo (Optional)
    import shutil
    cargo_path = shutil.which("cargo")
    if cargo_path:
        print(f"✔ Rust / Cargo: Installed at {cargo_path} (Optional: src/main.rs reference runner)")
    else:
        print("ℹ Rust / Cargo: Not found in PATH (Optional: only needed for src/main.rs reference runner)")

    if missing_required:
        print(f"\nMissing required packages: {', '.join(missing_required)}")
        should_install = auto_install
        if not auto_install and sys.stdin.isatty():
            ans = input("\nWould you like to install missing dependencies now? [Y/n]: ").strip().lower()
            should_install = ans in ("y", "yes", "")
        if should_install:
            import subprocess
            print("\nInstalling dependencies via pip...")
            cmd = [sys.executable, "-m", "pip", "install"] + missing_required
            res = subprocess.run(cmd)
            if res.returncode == 0:
                print("\n✔ All required dependencies successfully installed!")
                return True
            else:
                print("\n✖ Failed to install dependencies. Please run: pip install -r requirements.txt")
                return False
        return False

    print("\nVERDICT: Environment is 100% ready for assembling and validating court binders!")
    return True

def display_menu() -> None:
    """Prints the interactive wizard header and menu options to stdout."""
    print("================================================================================")
    print("    BRITISH COLUMBIA COURT APPLICATION RECORD MANAGER (PD-72 & CSO GUIDE)       ")
    print("================================================================================\n")
    print("Select an operation:")
    print("  1) Assemble Court Binder (from documents folder) [Primary]")
    print("  2) Validate Court Binder Submission (audit against 20 quality gates) [Primary]")
    print("  3) Run Full Closed-Loop Demo (Generate sample -> Assemble -> Audit)")
    print("  4) Generate synthetic test filings (discovery, amendment, or family)")
    print("  5) Check & Setup Environment (first-time dependencies & wheel verification)")
    print("  6) Exit")

def prompt_choice() -> str:
    """Prompts the operator for menu choice, defaulting to 1."""
    return input("\nEnter choice [1-6, default: 1]: ").strip() or "1"

def interactive_menu() -> tuple[str, str, str, str, bool]:
    """Interactive wizard coordinating user choices and file path resolution."""
    display_menu()
    choice = prompt_choice()

    if choice == "1":
        inputs_dir = input(f"Enter path to source documents folder [default: {DEFAULT_INPUTS_DIR}]: ").strip() or DEFAULT_INPUTS_DIR
        output_pdf = input(f"Enter destination PDF path [default: {DEFAULT_OUTPUT_PDF}]: ").strip() or DEFAULT_OUTPUT_PDF
        return "assemble", "discovery", inputs_dir, output_pdf, False

    elif choice == "2":
        pdf_path = input(f"Enter path to PDF binder to validate [default: {DEFAULT_OUTPUT_PDF}]: ").strip() or DEFAULT_OUTPUT_PDF
        return "validate", "discovery", "", pdf_path, False

    elif choice == "3":
        matter = input("Select matter type [discovery/amendment/family, default: discovery]: ").strip() or "discovery"
        inputs_dir = input(f"Input documents folder [default: {DEFAULT_INPUTS_DIR}]: ").strip() or DEFAULT_INPUTS_DIR
        output_pdf = input(f"Output PDF path [default: {DEFAULT_OUTPUT_PDF}]: ").strip() or DEFAULT_OUTPUT_PDF
        return "all", matter, inputs_dir, output_pdf, False

    elif choice == "4":
        matter = input("Select matter type [discovery/amendment/family, default: discovery]: ").strip() or "discovery"
        inputs_dir = input(f"Destination folder for filings [default: {DEFAULT_INPUTS_DIR}]: ").strip() or DEFAULT_INPUTS_DIR
        return "generate", matter, inputs_dir, "", False

    elif choice == "5":
        return "setup", "discovery", "", "", False

    else:
        print("Exiting.")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="BC Court Electronic Binder Lifecycle Manager (PD-72 & CSO Guide)."
    )
    parser.add_argument(
        "--mode",
        choices=["generate", "assemble", "validate", "all", "interactive", "setup"],
        default=None,
        help="Operational mode: generate, assemble, validate, all, setup, or interactive"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Launch interactive guided prompt menu"
    )
    parser.add_argument(
        "--matter-type",
        choices=["discovery", "amendment", "family"],
        default="discovery",
        help="Preset matter type for generation (default: discovery)"
    )
    parser.add_argument(
        "--inputs",
        default="inputs/01-commercial-discovery",
        help="Directory containing source filings and manifest.json"
    )
    parser.add_argument(
        "--output",
        default="output/01-commercial-discovery/Application_Record.pdf",
        help="Destination path for assembled court binder PDF"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON verification receipt"
    )

    args = parser.parse_args()

    mode = args.mode
    matter = args.matter_type
    inputs_dir = args.inputs
    output_pdf = args.output
    emit_json = args.json

    # Launch interactive menu if requested or run without arguments in a TTY
    if args.interactive or mode == "interactive" or (mode is None and sys.stdin.isatty() and len(sys.argv) == 1):
        mode, matter, inputs_dir, output_pdf, emit_json = interactive_menu()
    elif mode is None:
        mode = "all"

    # Mode 0: Setup
    if mode == "setup":
        success = check_or_setup_environment(auto_install=True)
        sys.exit(0 if success else 1)

    # Mode 1: Generate
    if mode in ("generate", "all"):
        print(f"=== [Step 1: Generating Input Filings ({matter})] ===")
        out_dir = Path(inputs_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(generating_court_documents, "generate_discovery_preset"):
            generating_court_documents.generate_discovery_preset(out_dir)

    # Mode 2: Assemble
    if mode in ("assemble", "all"):
        print(f"\n=== [Step 2: Assembling Electronic Court Binder] ===")
        in_path = Path(inputs_dir)
        out_path = Path(output_pdf)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        assembling_court_binders.build_binder(in_path, out_path)

    # Mode 3: Validate
    if mode in ("validate", "all"):
        print(f"\n=== [Step 3: Auditing Against 20 BC Court Quality Gates] ===")
        out_path = Path(output_pdf)
        passed, scorecard = validating_court_binders.validate_court_binder(out_path)
        if emit_json:
            import json
            print(json.dumps({"passed": passed, "scorecard": scorecard}, indent=2))
        else:
            for c in scorecard:
                if c["passed"]:
                    status_icon = "✔ PASS        "
                elif c["severity"] == "HARD_STOP":
                    status_icon = "✖ HARD_STOP   "
                else:
                    status_icon = "⚠ SOFT_WARNING"
                print(f"{status_icon} | [{c['rule']}] {c['title']}")
                print(f"       Authority: {c['authority']}")
                print(f"       Details:   {c['details']}")
                if not c["passed"]:
                    print(f"       Action:    {c['remediation']}")
                print("-" * 86)

            hard_stops = [c for c in scorecard if c["severity"] == "HARD_STOP" and not c["passed"]]
            soft_warnings = [c for c in scorecard if c["severity"] == "SOFT_WARNING" and not c["passed"]]
            passed_count = len([c for c in scorecard if c["passed"]])

            print("\nSUMMARY SCORECARD:")
            print(f"  - Hard Stops (Fatal Court Rejections): {len(hard_stops)}")
            print(f"  - Soft Warnings (Formatting Advisories): {len(soft_warnings)}")
            print(f"  - Passed Rules:                        {passed_count} / {len(scorecard)}")

            if len(hard_stops) == 0 and len(soft_warnings) == 0:
                verdict = "100% COMPLIANT - ALL GATES PASSED (APPROVED FOR CSO SUBMISSION)"
            elif len(hard_stops) == 0:
                verdict = "CONDITIONALLY COMPLIANT - PASS WITH SOFT WARNINGS (ACCEPTABLE FOR CSO)"
            else:
                verdict = "NON-COMPLIANT - REJECTED (HARD_STOP VIOLATIONS MUST BE REMEDIATED)"

            print(f"\nFINAL VERDICT: {verdict}")
        if not passed:
            sys.exit(1)

    print("\nSUCCESS: All requested operations completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
