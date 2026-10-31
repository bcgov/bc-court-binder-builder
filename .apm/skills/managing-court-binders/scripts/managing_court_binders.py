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

def main():
    parser = argparse.ArgumentParser(
        description="BC Court Electronic Binder Lifecycle Manager (PD-72 & CSO Guide)."
    )
    parser.add_argument(
        "--mode",
        choices=["generate", "assemble", "validate", "all"],
        default="all",
        help="Operational mode: generate (inputs), assemble (binder), validate (audit), or all (end-to-end)"
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

    # Mode 1: Generate
    if args.mode in ("generate", "all"):
        print(f"=== [Step 1: Generating Input Filings ({args.matter_type})] ===")
        out_dir = Path(args.inputs)
        out_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(generating_court_documents, "generate_discovery_preset"):
            generating_court_documents.generate_discovery_preset(out_dir)

    # Mode 2: Assemble
    if args.mode in ("assemble", "all"):
        print(f"\n=== [Step 2: Assembling Electronic Court Binder] ===")
        inputs_dir = Path(args.inputs)
        output_pdf = Path(args.output)
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        assembling_court_binders.build_binder(inputs_dir, output_pdf)

    # Mode 3: Validate
    if args.mode in ("validate", "all"):
        print(f"\n=== [Step 3: Auditing Against 20 BC Court Quality Gates] ===")
        output_pdf = Path(args.output)
        passed, scorecard = validating_court_binders.validate_court_binder(output_pdf)
        if args.json:
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
