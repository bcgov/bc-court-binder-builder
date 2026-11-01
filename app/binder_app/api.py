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
    def run_full_cycle(self) -> dict:
        """Generate sample filings, assemble a binder and validate it."""
        return _safe(lambda: engine.run_full_cycle(engine.load_workspace()))

    # Feature 2: assemble a user's folder into a binder.
    def assemble(self, inputs_dir: str, output_name: str) -> dict:
        """Assemble a binder from a folder; the PDF is saved in the working folder.

        Args:
            inputs_dir: Folder containing the filings.
            output_name: File name for the binder (".pdf" added if missing).
        """
        def action() -> dict:
            name = Path(output_name.strip() or "Application_Record").name
            if not name.lower().endswith(".pdf"):
                name += ".pdf"
            return engine.assemble(Path(inputs_dir), engine.load_workspace() / name)

        return _safe(action)

    # Feature 3: validate a binder PDF.
    def validate(self, pdf_path: str) -> dict:
        """Validate a binder PDF against the 20 quality gates."""
        return _safe(lambda: engine.validate(Path(pdf_path)))

    # Preview a folder before building.
    def inspect_folder(self, folder: str) -> dict:
        """Return file counts for a chosen folder."""
        return _safe(lambda: engine.inspect_folder(Path(folder)))

    # Open a PDF in the default viewer.
    def open_file(self, path: str) -> dict:
        """Open path with the operating system's default application."""
        def action() -> dict:
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
            if sys.platform == "darwin":
                subprocess.run(["open", "-R", str(target)], check=True)
            elif sys.platform == "win32":
                subprocess.run(["explorer", f"/select,{target}"], check=False)
            else:
                subprocess.run(["xdg-open", str(target.parent)], check=True)
            return {}

        return _safe(action)
