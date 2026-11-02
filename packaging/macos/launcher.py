#!/usr/bin/env python
"""
launcher.py (Entry point for the packaged macOS app)
=====================================

Purpose:
    PyInstaller needs a plain script to start from. This one starts the
    desktop app exactly as `python -m binder_app.main` does.

Layer: Packaging
"""

from binder_app.main import main

if __name__ == "__main__":
    main()
