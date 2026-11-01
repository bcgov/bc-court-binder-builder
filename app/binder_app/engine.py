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
import threading
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

SCRIPTS_ENV_VAR = "BC_BINDER_SCRIPTS"
SKILL_RELATIVE_PATH = Path(".apm/skills/managing-court-binders/scripts")
BUNDLED_FOLDER_NAME = "engine_scripts"
SAMPLE_PDF_NAME = "Application_Record_Sample.pdf"

# redirect_stdout swaps process-wide state, so concurrent UI calls must not overlap.
_CAPTURE_LOCK = threading.Lock()


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
    with _CAPTURE_LOCK, contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        value = func(*args)
    return value, buffer.getvalue()


CSO_HOST = "justice.gov.bc.ca"
DEFAULT_DIRECT_UPLOAD_MB = 20
DEFAULT_MAX_MB = 50


# Load the shared list of official CSO pages from the skill's references.
def load_cso_links() -> dict:
    """Return the CSO links file shared with the agent skill.

    Every address must be https on justice.gov.bc.ca; anything else is rejected
    so the app can never be pointed at an arbitrary site.

    Returns:
        The parsed cso_links.json dictionary.

    Raises:
        ValueError: If a page address is not an https justice.gov.bc.ca URL.
    """
    path = locate_scripts_dir().parent / "references" / "cso_links.json"
    links = json.loads(path.read_text(encoding="utf-8"))
    for key, page in links["pages"].items():
        if not is_official_cso_url(page["url"]):
            raise ValueError(f"CSO link '{key}' must be an https {CSO_HOST} address.")
    return links


# Strictly check that a URL can only ever lead to the official CSO host.
def is_official_cso_url(url: str) -> bool:
    """Return True only for plain https URLs whose host is exactly CSO_HOST.

    Python and web browsers parse some malformed URLs differently (for example
    a backslash before an "@"), so anything unusual is rejected outright:
    whitespace, control characters, backslashes, user info and ports.

    Args:
        url: The address to check.

    Returns:
        True if the URL is safe to open in the user's browser.
    """
    if not isinstance(url, str) or any(ch in url for ch in "\\@") or any(ord(ch) <= 32 or ord(ch) == 127 for ch in url):
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc == CSO_HOST and parsed.port is None


# Decide how a binder of a given size must be uploaded to CSO.
def filing_route(size_bytes: int, links: dict | None = None) -> dict:
    """Return the CSO upload route for a binder of size_bytes.

    Up to the direct-upload limit the file is uploaded as normal; above it the
    Upload Large Files step comes first; above the maximum it cannot be filed.

    Args:
        size_bytes: Size of the binder PDF.
        links: Parsed cso_links.json (limits are read from it when given).

    Returns:
        Dictionary with the route, size in MB, a UI level and a plain message.
    """
    limits = (links or {}).get("limits", {})
    direct_mb = limits.get("direct_upload_mb", DEFAULT_DIRECT_UPLOAD_MB)
    max_mb = limits.get("max_mb", DEFAULT_MAX_MB)
    size_mb = size_bytes / (1024 * 1024)
    if size_mb > max_mb:
        route, level = "too_large", "danger"
        message = f"{size_mb:.1f} MB is over the {max_mb} MB limit. Reduce the file size before filing."
    elif size_mb > direct_mb:
        route, level = "large_file", "warning"
        message = (f"{size_mb:.1f} MB is over {direct_mb} MB. Use Upload Large Files in the CSO E-file "
                   "menu first, then pick the file from the Select Large File list. The upload stays "
                   "available for 3 hours.")
    else:
        route, level = "direct", "success"
        message = f"{size_mb:.1f} MB is under {direct_mb} MB, so you can upload it directly."
    return {"route": route, "size_mb": round(size_mb, 2), "level": level, "message": message}


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


# Where the chosen folders are remembered between launches.
def _settings_file() -> Path:
    """Return the path of the per-user settings file."""
    return Path.home() / ".bc_court_binder_settings.json"


# Read all remembered settings (empty if none or unreadable).
def _read_settings() -> dict:
    """Return the saved settings dictionary, or {} if it cannot be read."""
    try:
        data = json.loads(_settings_file().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


# Merge one setting into the saved settings without losing the others.
def _save_setting(key: str, value: str) -> None:
    """Save one setting, keeping every other saved setting."""
    settings = _read_settings()
    settings[key] = value
    _settings_file().write_text(json.dumps(settings), encoding="utf-8")


# Read the remembered working folder, falling back to the default.
def load_workspace() -> Path:
    """Return the saved working folder, or the default if none is saved."""
    saved = _read_settings().get("workspace")
    return Path(saved) if saved else default_workspace()


# Remember a working folder, creating it if needed.
def save_workspace(folder: Path) -> Path:
    """Create folder if needed, remember it, and return it."""
    folder.mkdir(parents=True, exist_ok=True)
    _save_setting("workspace", str(folder))
    return folder


# Default folder for finished binders, kept apart from source filings.
def default_output_dir() -> Path:
    """Return the default output folder for finished binders.

    In a repository checkout this is the repository's output/ folder (the
    repository keeps source filings in inputs/ and binders in output/); in a
    packaged app it is "Output" inside the Documents "BC Court Binder" folder.
    """
    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / SKILL_RELATIVE_PATH).is_dir():
        return repo_root / "output"
    return Path.home() / "Documents" / "BC Court Binder" / "Output"


# Read the remembered output folder, falling back to the default.
def load_output_dir() -> Path:
    """Return the saved output folder, or the default if none is saved."""
    saved = _read_settings().get("output_dir")
    return Path(saved) if saved else default_output_dir()


# Remember an output folder, creating it if needed.
def save_output_dir(folder: Path) -> Path:
    """Create folder if needed, remember it, and return it."""
    folder.mkdir(parents=True, exist_ok=True)
    _save_setting("output_dir", str(folder))
    return folder


# Pick a binder path that never silently overwrites an existing file.
def unique_pdf_path(folder: Path, name: str) -> Path:
    """Return folder/name, or folder/'name 2.pdf' (3, 4...) if that file exists.

    Args:
        folder: Destination folder.
        name: Desired file name ending in .pdf.

    Returns:
        A path that does not exist yet.
    """
    candidate = folder / name
    stem, counter = candidate.stem, 2
    while candidate.exists():
        candidate = folder / f"{stem} {counter}.pdf"
        counter += 1
    return candidate


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


# Case details, manifest writing and naming live in the skill (single engine).
def read_case_details(folder: Path) -> dict:
    """Return the title-page case details for folder (see the skill's assembler)."""
    return _load_module("assembling_court_binders").read_case_details(folder)


def save_case_details(folder: Path, details: dict) -> Path:
    """Validate details and write folder/manifest.json (see the skill's assembler)."""
    return _load_module("assembling_court_binders").save_case_details(folder, details)


def suggest_binder_name(folder: Path, application_date: str | None = None) -> str:
    """Suggest a binder file name for folder (see the skill's assembler)."""
    return _load_module("assembling_court_binders").suggest_binder_name(folder, application_date)


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
    warnings: list[str] = []
    if not (inputs_dir / "manifest.json").exists():
        warnings.append(
            "No manifest.json was found, so the court file number and registry on the "
            "title page are placeholders and exhibits are not bookmarked. Add a "
            "manifest.json and rebuild before filing."
        )
    return {
        "output_pdf": str(output_pdf),
        "size_bytes": output_pdf.stat().st_size,
        "log": log,
        "warnings": warnings,
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
def run_full_cycle(workspace: Path, output_root: Path | None = None) -> dict:
    """Run a complete test cycle: generate, assemble, then validate.

    Source filings go in a timestamped subfolder of workspace; the finished
    binder goes in a matching subfolder of output_root.

    Args:
        workspace: Parent folder for the generated filings.
        output_root: Parent folder for the binder (the saved output folder if omitted).

    Returns:
        Dictionary with both folders, generation, assembly and validation.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = f"Sample run {stamp}"
    run_dir = workspace / run_name
    output_dir = (output_root if output_root is not None else load_output_dir()) / run_name
    generated = generate_sample(run_dir / "filings")
    assembled = assemble(run_dir / "filings", output_dir / SAMPLE_PDF_NAME)
    validation = validate(Path(assembled["output_pdf"]))
    return {
        "run_dir": str(run_dir),
        "output_dir": str(output_dir),
        "generated": generated,
        "assembled": assembled,
        "validation": validation,
    }
