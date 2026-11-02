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


# Check the optional PdfCraft native engine by merging two tiny PDFs with it.
def pdfcraft_check(required: bool) -> bool:
    """Merge two generated PDFs with the pdfcraft wheel's native engine.

    Args:
        required: If True, a missing pdfcraft counts as a failure.

    Returns:
        True if pdfcraft is absent and not required, or if the merge worked.
    """
    import tempfile

    try:
        from pdfcraft import LocalClient, MergeOptions
    except ImportError:
        print("  pdfcraft native engine: not included" + (" (REQUIRED)" if required else ""))
        return not required

    import pypdf

    from binder_app import engine

    generator = engine._load_module("generating_court_documents")
    with tempfile.TemporaryDirectory() as tmp:
        inputs = []
        for n in (1, 2):
            path = Path(tmp) / f"in{n}.pdf"
            path.write_bytes(generator.create_multipage_pdf([{"header": f"PAGE {n}", "subtitle": "test", "lines": ["x"]}]))
            inputs.append(path)
        # output_filename must be a bare file name (the engine rejects path separators).
        result = LocalClient().merge(inputs, MergeOptions(output_filename="selftest-merged.pdf"))
        data = result.data if result.data is not None else Path(result.path).read_bytes()
        if result.path is not None:
            Path(result.path).unlink(missing_ok=True)
        pages = len(pypdf.PdfReader(__import__("io").BytesIO(data)).pages)
    print(f"  pdfcraft native engine: {'OK' if pages == 2 else 'FAILED'} (merged {pages} pages)")
    return pages == 2


# Prove the bundled engine works without opening a window.
def selftest() -> int:
    """Run a full sample cycle in a temporary folder and check the result.

    Used by the installer build to confirm that the packaged app contains the
    skill scripts, the CSO links file and every dependency.

    Returns:
        0 if the sample binder passed all 20 gates, 1 otherwise.
    """
    import tempfile

    from binder_app import engine

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = engine.run_full_cycle(root / "work", root / "out")
        validation = result["validation"]
        links = engine.load_cso_links()
    gates_ok = validation["total"] == 20 and validation["passed_count"] == 20
    print(f"SELFTEST engine: {validation['passed_count']}/{validation['total']} gates, {len(links['pages'])} CSO links")
    ok = pdfcraft_check("--require-pdfcraft" in sys.argv) and gates_ok
    print(f"SELFTEST {'OK' if ok else 'FAILED'}")
    print(f"  default working folder: {engine.default_workspace()}")
    print(f"  default output folder:  {engine.default_output_dir()}")
    return 0 if ok else 1


# Create the window and start the GUI loop.
def main() -> None:
    """Create the native window and run the app (or the self-test with --selftest)."""
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
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
