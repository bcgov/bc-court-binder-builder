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
import subprocess
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


class ValidatorAccuracyTest(unittest.TestCase):
    """Regression tests for validator accuracy findings from the code review."""

    @classmethod
    def setUpClass(cls) -> None:
        """Builds one sample binder shared by the tests in this class."""
        cls._tmp = tempfile.TemporaryDirectory()
        cls.workspace = Path(cls._tmp.name)
        result = engine.run_full_cycle(cls.workspace)
        cls.good_pdf = Path(result["assembled"]["output_pdf"])

    @classmethod
    def tearDownClass(cls) -> None:
        """Removes the shared temporary workspace."""
        cls._tmp.cleanup()

    @staticmethod
    def _failing(summary: dict) -> list[str]:
        """Returns the rule ids that failed in a validation summary."""
        return [c["rule"] for c in summary["checks"] if not c["passed"]]

    def test_wrong_folio_font_and_size_are_caught(self) -> None:
        """Gates 12-13 must inspect the folio (regular 10 pt), not any text in the file."""
        raw = self.good_pdf.read_bytes()
        stamp = b"/F1 15 Tf\n290 760 Td"
        self.assertIn(stamp, raw)
        bad = self.workspace / "bad_folio.pdf"
        bad.write_bytes(raw.replace(stamp, b"/F2 10 Tf\n290 760 Td"))
        failing = self._failing(engine.validate(bad))
        for rule in ("RULE-12", "RULE-13"):
            self.assertIn(rule, failing)

    def test_short_final_page_is_not_flagged_as_truncated(self) -> None:
        """Gate 18 must not reject a filing whose last page is short by design."""
        folder = self.workspace / "short"
        folder.mkdir()
        doc = {"item_num": 1, "title": "Tab 1 - Notice", "short_title": "Notice of Application",
               "filename": "Tab01_Notice.pdf", "exhibits": []}
        manifest = {"court": "Supreme Court of British Columbia", "registry": "Vancouver",
                    "file_number": "S-1", "documents": [doc]}
        (folder / "manifest.json").write_text(json.dumps(manifest))
        line = "The applicant seeks an order for production of documents under Rule seven point one."
        (folder / "Tab01_Notice.txt").write_text("\n".join([line] * 29))
        result = engine.assemble(folder, self.workspace / "short.pdf")
        content_failures = [
            c for c in engine.validate(Path(result["output_pdf"]))["checks"]
            if c["rule"] == "RULE-18" and "truncated" in c["details"]
        ]
        self.assertEqual(content_failures, [])

    def test_encrypted_pdf_reports_gate_zero(self) -> None:
        """An encrypted PDF must produce a RULE-00 failure, not an exception."""
        writer = pypdf.PdfWriter(clone_from=str(self.good_pdf))
        writer.encrypt("secret")
        enc = self.workspace / "encrypted.pdf"
        writer.write(str(enc))
        self.assertIn("RULE-00", self._failing(engine.validate(enc)))

    def test_oversize_message_does_not_say_below_threshold(self) -> None:
        """Gate 2 details must say the file exceeds the limit when it does."""
        big = self.workspace / "big.pdf"
        big.write_bytes(self.good_pdf.read_bytes() + b"\n%" + b"x" * (51 * 1024 * 1024))
        gate = next(c for c in engine.validate(big)["checks"] if c["rule"] == "RULE-02")
        self.assertFalse(gate["passed"])
        self.assertIn("exceeds", gate["details"])
        self.assertNotIn("well below", gate["details"])

    def test_cli_all_mode_writes_manifest_and_passes_all_gates(self) -> None:
        """The skill's --mode all must write manifest.json and score 20/20."""
        script = engine.locate_scripts_dir() / "managing_court_binders.py"
        out = self.workspace / "cli"
        proc = subprocess.run(
            [sys.executable, str(script), "--mode", "all", "--inputs", str(out / "in"),
             "--output", str(out / "Application_Record.pdf")],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout[-400:])
        self.assertTrue((out / "in" / "manifest.json").exists())
        self.assertIn("100% COMPLIANT", proc.stdout)

    def test_cli_rejects_unsupported_matter_type(self) -> None:
        """Asking to generate a family or amendment preset must fail, not emit discovery filings."""
        script = engine.locate_scripts_dir() / "managing_court_binders.py"
        proc = subprocess.run(
            [sys.executable, str(script), "--mode", "generate", "--matter-type", "family",
             "--inputs", str(self.workspace / "fam")],
            capture_output=True, text=True, timeout=60,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse((self.workspace / "fam" / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
