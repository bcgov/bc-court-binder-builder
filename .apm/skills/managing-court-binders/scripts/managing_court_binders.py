#!/usr/bin/env python3
"""
managing_court_binders.py
-------------------------
Unified CLI driver for BC Supreme Court Electronic Application Record & Book of Authorities lifecycle.
Provides 4 operating modes:
  1. generate: Creates synthetic multi-page chambers filings (Form 32, 33, Affidavits with Exhibits, Form 35, Authorities).
  2. assemble: Executes two-pass continuous foliation, index table layout, invisible rectangle hyperlinks, and outlines.
  3. validate: Audits assembled binder against the 20 statutory BC Court quality gates (CSO 50 MB, bookmarks, folios).
  4. all / e2e: Executes the closed-loop pipeline from generation through assembly and automated audit.
"""

import sys
import argparse
from pathlib import Path

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

def interactive_menu():
    """Interactive wizard for terminal users when run without arguments."""
    print("================================================================================")
    print("    BRITISH COLUMBIA COURT APPLICATION RECORD MANAGER (PD-72 & CSO GUIDE)       ")
    print("================================================================================\n")
    print("Select an operation:")
    print("  1) Run Full Closed-Loop Pipeline (Generate -> Assemble -> Audit) [Recommended]")
    print("  2) Assemble Binder from existing documents folder")
    print("  3) Validate / Audit an existing PDF binder against 20 quality gates")
    print("  4) Generate synthetic test filings (discovery, amendment, or family)")
    print("  5) Exit")

    choice = input("\nEnter choice [1-5, default: 1]: ").strip() or "1"

    if choice == "1":
        matter = input("Select matter type [discovery/amendment/family, default: discovery]: ").strip() or "discovery"
        inputs_dir = input(f"Input documents folder [default: inputs/01-commercial-discovery]: ").strip() or "inputs/01-commercial-discovery"
        output_pdf = input(f"Output PDF path [default: output/01-commercial-discovery/Application_Record.pdf]: ").strip() or "output/01-commercial-discovery/Application_Record.pdf"
        return "all", matter, inputs_dir, output_pdf, False

    elif choice == "2":
        inputs_dir = input("Enter path to source documents folder: ").strip() or "inputs/01-commercial-discovery"
        output_pdf = input("Enter destination PDF path: ").strip() or "output/01-commercial-discovery/Application_Record.pdf"
        return "assemble", "discovery", inputs_dir, output_pdf, False

    elif choice == "3":
        pdf_path = input("Enter path to PDF binder to validate: ").strip() or "output/01-commercial-discovery/Application_Record.pdf"
        return "validate", "discovery", "", pdf_path, False

    elif choice == "4":
        matter = input("Select matter type [discovery/amendment/family, default: discovery]: ").strip() or "discovery"
        inputs_dir = input(f"Destination folder for filings [default: inputs/01-commercial-discovery]: ").strip() or "inputs/01-commercial-discovery"
        return "generate", matter, inputs_dir, "", False

    else:
        print("Exiting.")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="BC Court Electronic Binder Lifecycle Manager (PD-72 & CSO Guide)."
    )
    parser.add_argument(
        "--mode",
        choices=["generate", "assemble", "validate", "all", "interactive"],
        default=None,
        help="Operational mode: generate, assemble, validate, all, or interactive"
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
            print(f"\nAudit complete: {'20/20 PASS - APPROVED FOR CSO' if passed else 'FAIL - GATES REJECTED'}")
        if not passed:
            sys.exit(1)

    print("\nSUCCESS: All requested operations completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
