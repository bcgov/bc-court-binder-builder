#!/usr/bin/env python
"""
main.py (Entry point)
=====================================

Purpose:
    Launches the BC court binder desktop app: a native window that renders
    the BC Government Design System UI and talks to the engine via Api.

Layer: Application / Entry point

Usage Examples:
    python -m binder_app.main

Key Functions:
    main()

Script Dependencies:
    pywebview, binder_app.api

Consumed by:
    packaging/binder_app.spec, python -m binder_app.main
"""

import sys
from pathlib import Path

import webview

from binder_app.api import Api

WINDOW_TITLE = "Court binder builder"
WINDOW_SIZE = (1200, 820)
MIN_SIZE = (920, 640)


# Find the UI folder in development or inside a packaged app.
def ui_index() -> Path:
    """Return the path to ui/index.html (dev checkout or PyInstaller bundle)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    ui_dir = base / "binder_app" / "ui" if hasattr(sys, "_MEIPASS") else base / "ui"
    return ui_dir / "index.html"


# Create the window and start the GUI loop.
def main() -> None:
    """Create the native window and run the app."""
    api = Api()
    window = webview.create_window(
        WINDOW_TITLE,
        url=str(ui_index()),
        js_api=api,
        width=WINDOW_SIZE[0],
        height=WINDOW_SIZE[1],
        min_size=MIN_SIZE,
    )
    api.attach(window)
    webview.start()


if __name__ == "__main__":
    main()
