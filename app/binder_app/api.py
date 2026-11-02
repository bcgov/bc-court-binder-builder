#!/usr/bin/env python
"""
api.py (Bridge)
=====================================

Purpose:
    Methods exposed to the web UI through pywebview's js_api. Every method
    returns {"ok": True, ...} or {"ok": False, "error": "..."} so the UI can
    show a friendly message and never sees a Python traceback.

Layer: Application / Bridge

Usage Examples:
    window = webview.create_window("Court binder builder", url, js_api=Api())

Key Functions:
    Api.pick_folder(), Api.pick_pdf(), Api.run_full_cycle(),
    Api.assemble(), Api.validate(), Api.reveal()

Script Dependencies:
    pywebview, binder_app.engine

Consumed by:
    binder_app/main.py, ui/app.js
"""

import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any, Callable

import webview

from binder_app import engine


# Wrap an engine call so failures become friendly error dictionaries.
def _safe(action: Callable[[], dict]) -> dict:
    """Run action and convert exceptions into an error dictionary.

    Args:
        action: Zero-argument callable returning a result dictionary.

    Returns:
        The action's result with ok=True, or {"ok": False, "error": message}.
    """
    try:
        return {"ok": True, **action()}
    except Exception as exc:  # surfaced to the user, not swallowed
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


class Api:
    """Python methods callable from the UI as window.pywebview.api.<name>()."""

    def __init__(self) -> None:
        """Create the bridge; the window is attached after creation."""
        self._window: Any = None

    # Remember the window so dialogs can be opened from the bridge.
    def attach(self, window: Any) -> None:
        """Attach the pywebview window used for native file dialogs."""
        self._window = window

    # Native folder chooser.
    def pick_folder(self) -> str | None:
        """Open a folder dialog and return the chosen path, or None."""
        chosen = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        return chosen[0] if chosen else None

    # Native PDF chooser.
    def pick_pdf(self) -> str | None:
        """Open a file dialog filtered to PDFs and return the path, or None."""
        chosen = self._window.create_file_dialog(
            webview.FileDialog.OPEN, file_types=("PDF files (*.pdf)",)
        )
        return chosen[0] if chosen else None

    # Working folder shown in the UI.
    def workspace(self) -> str:
        """Return the current working folder as text."""
        return str(engine.load_workspace())

    # Change the working folder (typed or browsed).
    def set_workspace(self, folder: str) -> dict:
        """Save a new working folder, creating it if it does not exist."""
        def action() -> dict:
            if not folder.strip():
                raise ValueError("Enter a folder path.")
            return {"workspace": str(engine.save_workspace(Path(folder.strip()).expanduser()))}

        return _safe(action)

    # Feature 1: generate sample filings and run the whole cycle.
    def run_full_cycle(self, filings_dir: str = "", output_root: str = "") -> dict:
        """Generate sample filings, assemble a binder and validate it.

        Args:
            filings_dir: Folder for the sample filings; empty means the working folder.
            output_root: Folder for the binder; empty means the output folder.
        """
        def action() -> dict:
            work = Path(filings_dir).expanduser() if filings_dir.strip() else engine.load_workspace()
            out = Path(output_root).expanduser() if output_root.strip() else engine.load_output_dir()
            return engine.run_full_cycle(work, out)

        return _safe(action)

    # Output folder shown in the UI.
    def output_dir(self) -> str:
        """Return the current output folder as text."""
        return str(engine.load_output_dir())

    # Change the output folder (browsed).
    def set_output_dir(self, folder: str) -> dict:
        """Save a new output folder, creating it if it does not exist."""
        def action() -> dict:
            if not folder.strip():
                raise ValueError("Enter a folder path.")
            return {"output_dir": str(engine.save_output_dir(Path(folder.strip()).expanduser()))}

        return _safe(action)

    # Suggested file name for a binder built from this folder.
    def suggest_binder_name(self, inputs_dir: str, application_date: str = "") -> str:
        """Return the suggested binder file name (without .pdf)."""
        return engine.suggest_binder_name(Path(inputs_dir), application_date or None)

    # Case details to prefill the form for a folder.
    def case_details(self, inputs_dir: str) -> dict:
        """Return the case details found in the folder's manifest, or empty defaults."""
        return _safe(lambda: engine.read_case_details(Path(inputs_dir)))

    # Where a binder built from this folder will be saved by default.
    def default_binder_dir(self, inputs_dir: str) -> str:
        """Return output folder / source folder name, the default save location."""
        return str(engine.load_output_dir() / Path(inputs_dir).name)

    # Feature 2: assemble a user's folder into a binder.
    def assemble(self, inputs_dir: str, output_name: str, save_dir: str = "", details: dict | None = None) -> dict:
        """Assemble a binder from a folder and save it in a chosen or default folder.

        Args:
            inputs_dir: Folder containing the filings.
            output_name: File name for the binder (".pdf" added if missing).
            save_dir: Folder to save into; empty means the output folder plus a
                subfolder named after the filings folder.
            details: Case details from the form; saved as manifest.json first.
        """
        def action() -> dict:
            name = Path(output_name.strip() or "Application_Record").name
            if not name.lower().endswith(".pdf"):
                name += ".pdf"
            if details is not None and any(str(v).strip() for k, v in details.items() if k != "court"):
                engine.save_case_details(Path(inputs_dir), details, require_all=False)
            folder = Path(save_dir).expanduser() if save_dir.strip() else Path(self.default_binder_dir(inputs_dir))
            folder.mkdir(parents=True, exist_ok=True)
            target = engine.unique_pdf_path(folder, name)
            result = engine.assemble(Path(inputs_dir), target)
            if target.name != name:
                result["warnings"] = [
                    f"A file named {name} already existed, so this binder was saved as {target.name}."
                ] + result.get("warnings", [])
            return result

        return _safe(action)

    # Feature 3: validate a binder PDF.
    def validate(self, pdf_path: str) -> dict:
        """Validate a binder PDF against the 20 quality gates."""
        return _safe(lambda: engine.validate(Path(pdf_path)))

    # Labels and verification date for the CSO page buttons.
    def cso_pages(self) -> dict:
        """Return the CSO page labels and when the addresses were verified."""
        def action() -> dict:
            links = engine.load_cso_links()
            labels = {key: page["label"] for key, page in links["pages"].items()}
            return {"verified_on": links["verified_on"], "labels": labels}

        return _safe(action)

    # Open one official CSO page in the user's own browser.
    def open_cso_page(self, key: str) -> dict:
        """Open a CSO page by key. Only addresses in cso_links.json can be opened."""
        def action() -> dict:
            page = engine.load_cso_links()["pages"].get(key)
            if page is None:
                raise ValueError("Unknown CSO page.")
            if not webbrowser.open(page["url"]):
                raise RuntimeError("Could not open your web browser.")
            return {"url": page["url"]}

        return _safe(action)

    # Work out how a binder must be uploaded to CSO.
    def filing_route(self, pdf_path: str) -> dict:
        """Return the CSO upload route for the chosen binder PDF."""
        def action() -> dict:
            target = Path(pdf_path)
            if not target.is_file():
                raise FileNotFoundError(f"File not found: {pdf_path}")
            return engine.filing_route(target.stat().st_size, engine.load_cso_links())

        return _safe(action)

    # Preview a folder before building.
    def inspect_folder(self, folder: str) -> dict:
        """Return file counts for a chosen folder."""
        return _safe(lambda: engine.inspect_folder(Path(folder)))

    # Open a PDF in the default viewer.
    def open_file(self, path: str) -> dict:
        """Open path with the operating system's default application."""
        def action() -> dict:
            target = Path(path)
            if target.suffix.lower() != ".pdf" or not target.is_file():
                raise ValueError("Only existing PDF files can be opened.")
            if sys.platform == "darwin":
                subprocess.run(["open", path], check=True)
            elif sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.run(["xdg-open", path], check=True)
            return {}

        return _safe(action)

    # Show a file or folder in Finder or Explorer.
    def reveal(self, path: str) -> dict:
        """Reveal path in the operating system's file manager."""
        def action() -> dict:
            target = Path(path)
            if not target.exists():
                raise ValueError("That path no longer exists.")
            if sys.platform == "darwin":
                subprocess.run(["open", "-R", str(target)], check=True)
            elif sys.platform == "win32":
                subprocess.run(["explorer", f"/select,{target}"], check=False)
            else:
                subprocess.run(["xdg-open", str(target.parent)], check=True)
            return {}

        return _safe(action)
