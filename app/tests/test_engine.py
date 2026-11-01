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
from binder_app.api import Api


class EngineCycleTest(unittest.TestCase):
    """Runs the full generate, assemble and validate cycle."""

    def test_full_cycle_passes_all_gates(self) -> None:
        """The sample cycle must produce a binder that passes all 20 gates."""
        with tempfile.TemporaryDirectory() as tmp:
            result = engine.run_full_cycle(Path(tmp), Path(tmp) / "out")
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
        result = engine.run_full_cycle(cls.workspace, cls.workspace / "out")
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


class OutputFolderTest(unittest.TestCase):
    """Tests for where binders are saved."""

    def test_sample_cycle_keeps_filings_and_binder_in_separate_folders(self) -> None:
        """Filings go to the working folder and the binder to the output folder."""
        with tempfile.TemporaryDirectory() as tmp:
            work, out = Path(tmp) / "work", Path(tmp) / "out"
            result = engine.run_full_cycle(work, out)
            self.assertTrue(Path(result["run_dir"]).is_relative_to(work))
            self.assertTrue(Path(result["assembled"]["output_pdf"]).is_relative_to(out))
            self.assertFalse(list(work.rglob("*.pdf.pdf")))
            self.assertFalse(list(work.glob("*/Application_Record_Sample.pdf")))

    def test_unique_pdf_path_never_overwrites(self) -> None:
        """An existing binder is kept; the new one gets a numbered name."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "Binder.pdf").write_bytes(b"x")
            self.assertEqual(engine.unique_pdf_path(folder, "Binder.pdf").name, "Binder 2.pdf")
            (folder / "Binder 2.pdf").write_bytes(b"x")
            self.assertEqual(engine.unique_pdf_path(folder, "Binder.pdf").name, "Binder 3.pdf")
            self.assertEqual(engine.unique_pdf_path(folder, "Other.pdf").name, "Other.pdf")

    def test_api_saves_binder_in_chosen_folder_not_the_filings_folder(self) -> None:
        """The API builds into the folder the user chose and reports a renamed file."""
        with tempfile.TemporaryDirectory() as tmp:
            filings = Path(tmp) / "filings"
            filings.mkdir()
            _make_filing_pdf(filings, "Tab01_Notice_15Nov2026.pdf", "SAVE-LOCATION-TEST")
            save = Path(tmp) / "chosen"
            api = Api()
            first = api.assemble(str(filings), "Binder", str(save))
            second = api.assemble(str(filings), "Binder", str(save))
            self.assertTrue(first["ok"] and second["ok"], (first, second))
            self.assertEqual(Path(first["output_pdf"]).parent, save)
            self.assertEqual(Path(second["output_pdf"]).name, "Binder 2.pdf")
            self.assertTrue(any("already existed" in w for w in second["warnings"]))
            self.assertEqual(list(filings.glob("*.pdf")), [filings / "Tab01_Notice_15Nov2026.pdf"])

    def test_suggested_binder_name_uses_folder_and_application_date(self) -> None:
        """The suggested name is Application_Record_<folder>, plus DDMmmYYYY when the manifest has a date."""
        with tempfile.TemporaryDirectory() as tmp:
            plain = Path(tmp) / "02 amendment (draft)"
            plain.mkdir()
            self.assertEqual(engine.suggest_binder_name(plain), "Application_Record_02_amendment_draft")
            dated = Path(tmp) / "01-commercial-discovery"
            dated.mkdir()
            (dated / "manifest.json").write_text(json.dumps({"application_date": "December 4, 2026 at 9:45 AM"}))
            self.assertEqual(engine.suggest_binder_name(dated), "Application_Record_01-commercial-discovery_04Dec2026")

    def test_settings_keep_both_folders(self) -> None:
        """Saving one folder setting must not erase the other."""
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            engine, "_settings_file", return_value=Path(tmp) / "settings.json"
        ):
            engine.save_workspace(Path(tmp) / "work")
            engine.save_output_dir(Path(tmp) / "out")
            self.assertEqual(engine.load_workspace(), Path(tmp) / "work")
            self.assertEqual(engine.load_output_dir(), Path(tmp) / "out")


class CaseDetailsTest(unittest.TestCase):
    """Tests for the case-details form and manifest writing."""

    FULL = {
        "court": "Supreme Court of British Columbia", "registry": "Kelowna", "file_number": "S-98765",
        "plaintiff": "Roe Holdings Ltd.", "defendant": "Doe Corp.", "application_date": "March 3, 2027",
        "time_estimate": "20 minutes", "counsel_applicant": "", "counsel_respondent": "",
    }

    def test_details_are_required_and_defaults_empty(self) -> None:
        """Without a manifest the form starts empty (court prefilled) and blanks are refused."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            details = engine.read_case_details(folder)
            self.assertFalse(details["has_manifest"])
            self.assertEqual(details["file_number"], "")
            with self.assertRaises(ValueError) as ctx:
                engine.save_case_details(folder, {**self.FULL, "file_number": " "})
            self.assertIn("court file number", str(ctx.exception))
            _make_filing_pdf(folder, "Tab01_Notice_15Nov2026.pdf", "OPTIONAL-FIELD")
            engine.save_case_details(Path(tmp), {**self.FULL, "time_estimate": ""})
            self.assertNotIn("time_estimate", json.loads((Path(tmp) / "manifest.json").read_text()))

    def test_building_with_details_writes_manifest_and_real_title_page(self) -> None:
        """The API saves manifest.json and the binder shows the entered details, not placeholders."""
        with tempfile.TemporaryDirectory() as tmp:
            filings = Path(tmp) / "filings"
            filings.mkdir()
            _make_filing_pdf(filings, "Tab01_Notice_15Nov2026.pdf", "FORM-TEST")
            result = Api().assemble(str(filings), "Binder", str(Path(tmp) / "out"), self.FULL)
            self.assertTrue(result["ok"], result)
            self.assertTrue((filings / "manifest.json").is_file())
            self.assertEqual(result["warnings"], [])
            text = _binder_text(Path(result["output_pdf"]))
            self.assertIn("S-98765", text)
            self.assertIn("Roe Holdings Ltd.", text)
            self.assertNotIn("[Court file number", text)
            self.assertNotIn("S-240123", text)

    def test_optional_details_are_left_off_the_title_page(self) -> None:
        """A blank time estimate and blank counsel must not print invented defaults."""
        with tempfile.TemporaryDirectory() as tmp:
            filings = Path(tmp) / "filings"
            filings.mkdir()
            _make_filing_pdf(filings, "Tab01_Notice_15Nov2026.pdf", "OPTIONAL-TEST")
            details = {**self.FULL, "time_estimate": "", "counsel_applicant": "", "counsel_respondent": ""}
            result = Api().assemble(str(filings), "Binder", str(Path(tmp) / "out"), details)
            self.assertTrue(result["ok"], result)
            text = _binder_text(Path(result["output_pdf"]))
            self.assertIn("S-98765", text)
            self.assertNotIn("Time Estimate", text)
            self.assertNotIn("25 min", text)
            self.assertNotIn("Counsel of Record", text)
            self.assertNotIn("Counsel for", text)

    def test_provided_optional_details_are_printed(self) -> None:
        """A time estimate and counsel that the user entered appear on the title page."""
        with tempfile.TemporaryDirectory() as tmp:
            filings = Path(tmp) / "filings"
            filings.mkdir()
            _make_filing_pdf(filings, "Tab01_Notice_15Nov2026.pdf", "OPTIONAL-TEST")
            details = {**self.FULL, "time_estimate": "20 minutes", "counsel_applicant": "A. Lawyer"}
            result = Api().assemble(str(filings), "Binder", str(Path(tmp) / "out"), details)
            text = _binder_text(Path(result["output_pdf"]))
            self.assertIn("Time Estimate: 20 minutes", text)
            self.assertIn("Counsel for Applicant: A. Lawyer", text)

    def test_saving_keeps_existing_documents_and_exhibits(self) -> None:
        """Editing details in an existing manifest must not lose its documents."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            doc = {"item_num": 1, "title": "Tab 1 - X", "short_title": "X", "filename": "a.pdf",
                   "exhibits": [{"letter": "A", "description": "Agreement", "rel_page": 2}]}
            (folder / "manifest.json").write_text(json.dumps({"documents": [doc], "extra": "keep"}))
            engine.save_case_details(folder, self.FULL)
            saved = json.loads((folder / "manifest.json").read_text())
            self.assertEqual(saved["documents"], [doc])
            self.assertEqual(saved["extra"], "keep")
            self.assertEqual(saved["file_number"], "S-98765")

    def test_cli_case_flags_write_manifest_and_real_title_page(self) -> None:
        """The skill's command line accepts case details, writes manifest.json and never uses sample values."""
        with tempfile.TemporaryDirectory() as tmp:
            filings = Path(tmp) / "filings"
            filings.mkdir()
            _make_filing_pdf(filings, "Tab01_Notice_15Nov2026.pdf", "CLI-FORM-TEST")
            out = Path(tmp) / "Binder.pdf"
            script = engine.locate_scripts_dir() / "managing_court_binders.py"
            proc = subprocess.run(
                [sys.executable, str(script), "--mode", "assemble", "--inputs", str(filings), "--output", str(out),
                 "--registry", "Kelowna", "--file-number", "S-55555", "--plaintiff", "A Ltd.", "--defendant", "B Corp.",
                 "--hearing-date", "March 3, 2027", "--time-estimate", "20 minutes"],
                capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout[-400:] + proc.stderr[-400:])
            self.assertTrue((filings / "manifest.json").is_file())
            text = _binder_text(out)
            self.assertIn("S-55555", text)
            self.assertNotIn("S-240123", text)
            self.assertNotIn("WARNING", proc.stdout)

    def test_cli_warns_when_no_case_details_exist(self) -> None:
        """With no manifest and no case flags the CLI must warn that the title page has placeholders."""
        with tempfile.TemporaryDirectory() as tmp:
            filings = Path(tmp) / "filings"
            filings.mkdir()
            _make_filing_pdf(filings, "Tab01_Notice_15Nov2026.pdf", "NO-DETAILS")
            script = engine.locate_scripts_dir() / "managing_court_binders.py"
            proc = subprocess.run(
                [sys.executable, str(script), "--mode", "assemble", "--inputs", str(filings), "--output", str(Path(tmp) / "b.pdf")],
                capture_output=True, text=True, timeout=120,
            )
            self.assertIn("WARNING: no manifest.json", proc.stdout)

    def test_suggested_name_uses_typed_date(self) -> None:
        """A date typed in the form overrides the manifest date in the suggested name."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "matter"
            folder.mkdir()
            self.assertEqual(engine.suggest_binder_name(folder, "March 3, 2027"), "Application_Record_matter_03Mar2027")


class CsoGuideTest(unittest.TestCase):
    """Tests for the CSO links, upload route and the page-opening API."""

    def test_links_file_only_contains_official_cso_addresses(self) -> None:
        """Every shared CSO address must be https on justice.gov.bc.ca."""
        links = engine.load_cso_links()
        self.assertTrue({"register", "logon", "efile_home"} <= set(links["pages"]))
        for page in links["pages"].values():
            self.assertTrue(page["url"].startswith("https://justice.gov.bc.ca/"))

    def test_loader_rejects_foreign_hosts(self) -> None:
        """A links file pointing at another site must be refused."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "scripts").mkdir()
            refs = Path(tmp) / "references"
            refs.mkdir()
            bad = {"verified_on": "x", "pages": {"evil": {"label": "x", "url": "https://example.com/cso"}}}
            (refs / "cso_links.json").write_text(json.dumps(bad))
            with mock.patch.object(engine, "locate_scripts_dir", return_value=Path(tmp) / "scripts"):
                with self.assertRaises(ValueError):
                    engine.load_cso_links()

    def test_filing_route_boundaries(self) -> None:
        """20 MB and under uploads directly; over 20 needs large file upload; over 50 is blocked."""
        mb = 1024 * 1024
        links = engine.load_cso_links()
        self.assertEqual(engine.filing_route(5 * mb, links)["route"], "direct")
        self.assertEqual(engine.filing_route(20 * mb, links)["route"], "direct")
        self.assertEqual(engine.filing_route(21 * mb, links)["route"], "large_file")
        self.assertEqual(engine.filing_route(50 * mb, links)["route"], "large_file")
        self.assertEqual(engine.filing_route(51 * mb, links)["route"], "too_large")

    def test_url_guard_rejects_parser_differentials(self) -> None:
        """Addresses that Python and browsers read differently must be rejected."""
        good = "https://justice.gov.bc.ca/cso/register.do"
        self.assertTrue(engine.is_official_cso_url(good))
        for bad in (
            "https://evil.com\\@justice.gov.bc.ca/cso",
            "https://justice.gov.bc.ca\\@evil.com/",
            "https://user@justice.gov.bc.ca/cso",
            "https://justice.gov.bc.ca:8443/cso",
            "https://justice.gov.bc.ca/cso\nhttps://evil.com",
            "http://justice.gov.bc.ca/cso",
            "https://justice.gov.bc.ca.evil.com/cso",
        ):
            self.assertFalse(engine.is_official_cso_url(bad), bad)

    def test_ambiguous_prefix_text_files_are_refused(self) -> None:
        """Two text files sharing a filing's prefix must raise, not pick one silently."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "in"
            folder.mkdir()
            doc = {"item_num": 1, "title": "Tab 1 - X", "short_title": "X", "filename": "01_Notice.pdf", "exhibits": []}
            (folder / "manifest.json").write_text(json.dumps({"documents": [doc]}))
            (folder / "01_Draft_one.txt").write_text("alpha " * 30)
            (folder / "01_Draft_two.txt").write_text("beta " * 30)
            with self.assertRaises(ValueError):
                engine.assemble(folder, Path(tmp) / "out.pdf")

    def test_open_cso_page_opens_only_listed_pages(self) -> None:
        """The API opens a known page and refuses any other key without opening a browser."""
        api = Api()
        with mock.patch("webbrowser.open", return_value=True) as opener:
            ok = api.open_cso_page("register")
            self.assertTrue(ok["ok"])
            opener.assert_called_once_with("https://justice.gov.bc.ca/cso/register.do")
            opener.reset_mock()
            refused = api.open_cso_page("https://example.com")
            self.assertFalse(refused["ok"])
            opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
