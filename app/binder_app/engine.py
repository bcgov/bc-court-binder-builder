#!/usr/bin/env python
"""
engine.py (Adapter)
=====================================

Purpose:
    Thin adapter between the desktop app and the managing-court-binders skill
    scripts. The skill stays the single source of truth for generating,
    assembling and validating court binders; this module only locates and
    imports it, captures its console output, and shapes results for the UI.

Layer: Application / Adapter

Usage Examples:
    from binder_app import engine
    result = engine.run_full_cycle(engine.default_workspace())

Input Files:
    Skill scripts in .apm/skills/managing-court-binders/scripts/ (development)
    or the bundled engine_scripts/ folder (packaged app).

Output:
    JSON-serialisable dictionaries consumed by binder_app.api.

Key Functions:
    locate_scripts_dir(), generate_sample(), assemble(), validate(),
    run_full_cycle(), summarise_scorecard()

Script Dependencies:
    pypdf, pdfplumber (via the skill scripts)

Consumed by:
    binder_app/api.py, tests/test_engine.py
"""

import contextlib
import importlib
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

SCRIPTS_ENV_VAR = "BC_BINDER_SCRIPTS"
SKILL_RELATIVE_PATH = Path(".apm/skills/managing-court-binders/scripts")
BUNDLED_FOLDER_NAME = "engine_scripts"
SAMPLE_PDF_NAME = "Application_Record_Sample.pdf"


# Locate the folder holding the skill scripts (env override, bundle, or repo).
def locate_scripts_dir() -> Path:
    """Return the directory that contains the skill's Python scripts.

    Resolution order: the BC_BINDER_SCRIPTS environment variable, the folder
    bundled by PyInstaller, then the repository's skill folder.

    Returns:
        Path to the scripts directory.

    Raises:
        FileNotFoundError: If no candidate directory exists.
    """
    candidates: list[Path] = []
    override = os.environ.get(SCRIPTS_ENV_VAR)
    if override:
        candidates.append(Path(override))
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.append(Path(bundle_root) / BUNDLED_FOLDER_NAME)
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / SKILL_RELATIVE_PATH)

    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not find the managing-court-binders scripts. Searched: "
        + ", ".join(str(c) for c in candidates)
    )


# Import one skill module after making its folder importable.
def _load_module(name: str) -> ModuleType:
    """Import a skill script by module name.

    Args:
        name: Module name, such as "validating_court_binders".

    Returns:
        The imported module.
    """
    scripts_dir = str(locate_scripts_dir())
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return importlib.import_module(name)


# Run a callable while capturing anything the skill prints.
def _capture(func: Any, *args: Any) -> tuple[Any, str]:
    """Call func(*args) and return its result with captured console output.

    Args:
        func: Callable to run.
        *args: Positional arguments for the callable.

    Returns:
        Tuple of (return value, captured stdout and stderr text).
    """
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        value = func(*args)
    return value, buffer.getvalue()


# Default folder where the app writes everything it creates.
def default_workspace() -> Path:
    """Return the default working folder.

    In a repository checkout this is the repository's inputs/ folder;
    in a packaged app it is "BC Court Binder" under the user's Documents.
    """
    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / SKILL_RELATIVE_PATH).is_dir():
        return repo_root / "inputs"
    return Path.home() / "Documents" / "BC Court Binder"


# Where the chosen working folder is remembered between launches.
def _settings_file() -> Path:
    """Return the path of the per-user settings file."""
    return Path.home() / ".bc_court_binder_settings.json"


# Read the remembered working folder, falling back to the default.
def load_workspace() -> Path:
    """Return the saved working folder, or the default if none is saved."""
    try:
        saved = json.loads(_settings_file().read_text(encoding="utf-8"))
        return Path(saved["workspace"])
    except (OSError, ValueError, KeyError):
        return default_workspace()


# Remember a working folder, creating it if needed.
def save_workspace(folder: Path) -> Path:
    """Create folder if needed, remember it, and return it.

    Args:
        folder: The working folder chosen by the user.

    Returns:
        The folder that was saved.
    """
    folder.mkdir(parents=True, exist_ok=True)
    _settings_file().write_text(json.dumps({"workspace": str(folder)}), encoding="utf-8")
    return folder


# Turn a raw scorecard into totals and a plain-language verdict.
def summarise_scorecard(passed: bool, scorecard: list[dict]) -> dict:
    """Summarise validation checks using the skill's verdict wording.

    Args:
        passed: True when the validator found no HARD_STOP failures.
        scorecard: Check dictionaries from validate_court_binder().

    Returns:
        Dictionary with counts, a verdict level and the checks themselves.
    """
    hard = [c for c in scorecard if c["severity"] == "HARD_STOP" and not c["passed"]]
    soft = [c for c in scorecard if c["severity"] == "SOFT_WARNING" and not c["passed"]]
    if not hard and not soft:
        level, verdict = "success", "All gates passed. Ready for Court Services Online."
    elif not hard:
        level, verdict = "warning", "Passed with formatting advisories."
    else:
        level, verdict = "danger", "Not compliant. Fix the hard stops before filing."
    return {
        "passed": passed,
        "level": level,
        "verdict": verdict,
        "total": len(scorecard),
        "passed_count": len([c for c in scorecard if c["passed"]]),
        "hard_stops": len(hard),
        "soft_warnings": len(soft),
        "checks": scorecard,
    }


# Count what is in a folder so the UI can preview it before building.
def inspect_folder(folder: Path) -> dict:
    """Summarise the filings in folder.

    Args:
        folder: Folder the user chose.

    Returns:
        Dictionary with PDF and text file counts and whether manifest.json exists.

    Raises:
        FileNotFoundError: If folder does not exist.
    """
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")
    names = [f.name.lower() for f in folder.iterdir() if f.is_file()]
    return {
        "pdf_count": sum(n.endswith(".pdf") for n in names),
        "txt_count": sum(n.endswith(".txt") for n in names),
        "has_manifest": "manifest.json" in names,
    }


# Create the sample filings used for a full test cycle.
def generate_sample(inputs_dir: Path) -> dict:
    """Generate the sample discovery filings and manifest.json.

    Args:
        inputs_dir: Folder that will receive the generated filings.

    Returns:
        Dictionary with the folder path, document count and console log.
    """
    generator = _load_module("generating_court_documents")
    inputs_dir.mkdir(parents=True, exist_ok=True)
    manifest, log = _capture(generator.generate_discovery_preset, inputs_dir)
    # The generator returns the manifest but only its own CLI writes it to
    # disk; the assembler needs it to create exhibit sub-bookmarks (RULE-18).
    (inputs_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "inputs_dir": str(inputs_dir),
        "document_count": len(manifest.get("documents", [])),
        "log": log,
    }


# Assemble a folder of filings into a foliated, bookmarked binder PDF.
def assemble(inputs_dir: Path, output_pdf: Path) -> dict:
    """Assemble the filings in inputs_dir into one binder PDF.

    Args:
        inputs_dir: Folder with the source filings (manifest.json optional).
        output_pdf: Destination path of the binder.

    Returns:
        Dictionary with the output path, size in bytes and console log.

    Raises:
        FileNotFoundError: If inputs_dir does not exist.
    """
    if not inputs_dir.is_dir():
        raise FileNotFoundError(f"Folder not found: {inputs_dir}")
    assembler = _load_module("assembling_court_binders")
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    _, log = _capture(assembler.build_binder, inputs_dir, output_pdf)
    return {
        "output_pdf": str(output_pdf),
        "size_bytes": output_pdf.stat().st_size,
        "log": log,
    }


# Audit a binder PDF against the 20 BC court quality gates.
def validate(pdf_path: Path) -> dict:
    """Validate a binder PDF and return the summarised scorecard.

    Args:
        pdf_path: Path to the binder PDF.

    Returns:
        Summary dictionary from summarise_scorecard() plus the file path.
    """
    validator = _load_module("validating_court_binders")
    (passed, scorecard), _ = _capture(validator.validate_court_binder, pdf_path)
    summary = summarise_scorecard(passed, scorecard)
    summary["file"] = str(pdf_path)
    return summary


# Run generate, assemble and validate in a fresh timestamped folder.
def run_full_cycle(workspace: Path) -> dict:
    """Run a complete test cycle: generate, assemble, then validate.

    Args:
        workspace: Parent folder; a timestamped run folder is created inside.

    Returns:
        Dictionary with the run folder, generation, assembly and validation.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = workspace / f"Sample run {stamp}"
    generated = generate_sample(run_dir / "filings")
    assembled = assemble(run_dir / "filings", run_dir / SAMPLE_PDF_NAME)
    validation = validate(Path(assembled["output_pdf"]))
    return {
        "run_dir": str(run_dir),
        "generated": generated,
        "assembled": assembled,
        "validation": validation,
    }
