# -*- mode: python ; coding: utf-8 -*-
"""
binder_app.spec (PyInstaller specification for the macOS app)
=====================================

Purpose:
    Builds "Court binder builder.app". The app bundles:
      * the desktop app (binder_app, including the UI and BC Sans fonts),
      * the managing-court-binders skill scripts (engine_scripts/), which the app
        imports as its engine, and
      * the CSO links file from the skill's references (references/).

Layer: Packaging
Run with: packaging/macos/build_dmg.sh (not directly).
"""

from pathlib import Path

ROOT = Path(SPECPATH).resolve().parents[1]
APP_DIR = ROOT / "app"
SKILL = ROOT / ".apm" / "skills" / "managing-court-binders"
SCRIPTS = SKILL / "scripts"

import importlib.util

spec_version = importlib.util.spec_from_file_location("v", APP_DIR / "binder_app" / "__init__.py")
VERSION = "0.1.0"
for line in (APP_DIR / "binder_app" / "__init__.py").read_text().splitlines():
    if line.startswith("__version__"):
        VERSION = line.split("=")[1].strip().strip('"')

datas = [
    (str(APP_DIR / "binder_app" / "ui"), "binder_app/ui"),
    (str(SKILL / "references" / "cso_links.json"), "references"),
]
for script in ("assembling_court_binders.py", "generating_court_documents.py", "validating_court_binders.py"):
    datas.append((str(SCRIPTS / script), "engine_scripts"))

# The optional PdfCraft native engine (the pdfcraft wheel: Python wrappers plus the compiled
# Rust library). It is bundled when the build environment has it installed.
HAS_PDFCRAFT = importlib.util.find_spec("pdfcraft") is not None
PDFCRAFT_IMPORTS = [
    "pdfcraft", "pdfcraft.local", "pdfcraft.session", "pdfcraft.types", "pdfcraft.errors",
    "pdfcraft.rest", "pdfcraft._native", "PIL", "PIL.Image",
] if HAS_PDFCRAFT else []

a = Analysis(
    [str(Path(SPECPATH) / "launcher.py")],
    pathex=[str(APP_DIR), str(SCRIPTS)],
    datas=datas,
    # The engine imports these by name at run time, so list them for analysis.
    hiddenimports=[
        "assembling_court_binders",
        "generating_court_documents",
        "validating_court_binders",
        "pypdf",
        "webview.platforms.cocoa",
    ] + PDFCRAFT_IMPORTS,
    excludes=["tkinter", "pdfplumber"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Court binder builder",
    console=False,
    argv_emulation=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="Court binder builder")
app = BUNDLE(
    coll,
    name="Court binder builder.app",
    bundle_identifier="ca.gov.bc.courtbinderbuilder",
    version=VERSION,
    info_plist={
        "CFBundleDisplayName": "Court binder builder",
        "CFBundleShortVersionString": VERSION,
        "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.productivity",
    },
)
