#!/usr/bin/env python
"""
test_engine.py (Test)
=====================================

Purpose:
    End-to-end check that the engine adapter can generate sample filings,
    assemble a binder and validate it using the real skill scripts.

Layer: Test

Usage Examples:
    app/.venv/bin/python -m unittest discover -s app/tests -t app

Consumed by:
    Developers and CI.
"""

import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import pypdf

from binder_app import engine


class EngineCycleTest(unittest.TestCase):
    """Runs the full generate, assemble and validate cycle."""

    def test_full_cycle_passes_all_gates(self) -> None:
        """The sample cycle must produce a binder that passes all 20 gates."""
        with tempfile.TemporaryDirectory() as tmp:
            result = engine.run_full_cycle(Path(tmp))
            validation = result["validation"]
            self.assertTrue(Path(result["assembled"]["output_pdf"]).exists())
            self.assertEqual(validation["total"], 20)
            self.assertEqual(validation["level"], "success", validation["verdict"])

    def test_validate_missing_file_raises(self) -> None:
        """Validating a path that does not exist raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            engine.validate(Path("/nonexistent/binder.pdf"))


def _make_filing_pdf(folder: Path, name: str, marker: str) -> None:
    """Writes a one-page text PDF containing marker using the skill's generator."""
    generator = engine._load_module("generating_court_documents")
    page = {"header": "NOTICE OF APPLICATION", "subtitle": marker, "lines": [f"{marker} " + "word " * 20]}
    (folder / name).write_bytes(generator.create_multipage_pdf([page]))


def _binder_text(pdf: Path) -> str:
    """Returns all text in a PDF."""
    return "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(str(pdf)).pages)


class SecurityRegressionTest(unittest.TestCase):
    """Regression tests for the forensic audit findings."""

    def test_source_content_survives_without_pdftotext(self) -> None:
        """F1: real filing text must reach the binder even when pdftotext is missing."""
        with tempfile.TemporaryDirectory() as tmp, mock.patch("shutil.which", return_value=None):
            folder = Path(tmp) / "in"
            folder.mkdir()
            _make_filing_pdf(folder, "Tab01_Notice_15Nov2026.pdf", "ZEBRA-MARKER-123")
            out = Path(tmp) / "out.pdf"
            engine.assemble(folder, out)
            text = _binder_text(out)
            self.assertIn("ZEBRA-MARKER-123", text)
            self.assertNotIn("Substantive legal content filed with court", text)

    def test_unreadable_source_fails_instead_of_placeholder(self) -> None:
        """F1: a filing with no recoverable text must raise, never be replaced."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "in"
            folder.mkdir()
            writer = pypdf.PdfWriter()
            writer.add_blank_page(612, 792)
            with (folder / "Tab01_Scan_15Nov2026.pdf").open("wb") as fh:
                writer.write(fh)
            with self.assertRaises(ValueError):
                engine.assemble(folder, Path(tmp) / "out.pdf")

    def test_inferred_manifest_never_invents_court_details(self) -> None:
        """F2: without manifest.json the title page must not carry the sample file number."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "in"
            folder.mkdir()
            _make_filing_pdf(folder, "Tab01_Notice_15Nov2026.pdf", "CLIENT-MATTER")
            result = engine.assemble(folder, Path(tmp) / "out.pdf")
            self.assertNotIn("S-240123", _binder_text(Path(result["output_pdf"])))
            self.assertTrue(result["warnings"])

    def test_manifest_cannot_read_outside_input_folder(self) -> None:
        """F3: a manifest filename that escapes the folder is rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "secret.txt").write_text("PRIVILEGED " * 10)
            folder = root / "in"
            folder.mkdir()
            doc = {"item_num": 1, "title": "Tab 1 - X", "short_title": "X", "filename": "../secret.txt", "exhibits": []}
            (folder / "manifest.json").write_text(json.dumps({"documents": [doc]}))
            with self.assertRaises(ValueError):
                engine.assemble(folder, root / "out.pdf")

    def test_validator_rejects_unreadable_pdf_clearly(self) -> None:
        """F4: garbage input raises a ValueError naming the problem, not AttributeError."""
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "garbage.pdf"
            bad.write_bytes(b"not a pdf")
            with self.assertRaises(ValueError):
                engine.validate(bad)

    def test_concurrent_capture_restores_stdout(self) -> None:
        """F5: overlapping captures must leave sys.stdout untouched."""
        original = sys.stdout

        def slow() -> None:
            time.sleep(0.2)
            print("x")

        threads = [threading.Thread(target=engine._capture, args=(slow,)) for _ in range(2)]
        for t in threads:
            t.start()
            time.sleep(0.05)
        for t in threads:
            t.join()
        self.assertIs(sys.stdout, original)


if __name__ == "__main__":
    unittest.main()
