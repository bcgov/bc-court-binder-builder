# -*- mode: python ; coding: utf-8 -*-
"""
binder_app.spec (PyInstaller specification for the Windows app)
=====================================

Purpose:
    Builds the "Court binder builder" folder (an .exe plus its libraries). The app bundles:
      * the desktop app (binder_app, including the UI and BC Sans fonts),
      * the managing-court-binders skill scripts (engine_scripts/), which the app
        imports as its engine, and
      * the CSO links file from the skill's references (references/).
    The optional PdfCraft native engine is bundled when the pdfcraft wheel is installed in
    the build environment (no Windows wheel is published yet; see README.md).

Layer: Packaging
Run with: packaging/windows/package.ps1 (not directly).
"""

import importlib.util
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parents[1]
APP_DIR = ROOT / "app"
SKILL = ROOT / ".apm" / "skills" / "managing-court-binders"
SCRIPTS = SKILL / "scripts"

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
        # pywebview on Windows draws with Microsoft Edge WebView2 through pythonnet.
        "webview.platforms.edgechromium",
        "webview.platforms.winforms",
        "clr_loader",
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
    console=False,  # a windowed app has no console; the self-test writes its result to a file
)
coll = COLLECT(exe, a.binaries, a.datas, name="Court binder builder")
