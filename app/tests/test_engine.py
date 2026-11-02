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

    def test_textless_pdf_is_kept_as_a_true_copy_and_flagged_by_the_validator(self) -> None:
        """A page with no text (a scan) is not replaced by placeholder text; the validator flags it."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "in"
            folder.mkdir()
            writer = pypdf.PdfWriter()
            writer.add_blank_page(612, 792)
            with (folder / "Tab01_Scan_15Nov2026.pdf").open("wb") as fh:
                writer.write(fh)
            result = engine.assemble(folder, Path(tmp) / "out.pdf")
            text = _binder_text(Path(result["output_pdf"]))
            self.assertNotIn("Substantive legal content filed with court", text)
            checks = {c["rule"]: c for c in engine.validate(Path(result["output_pdf"]))["checks"]}
            self.assertFalse(checks["RULE-18"]["passed"])

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
        assembler = engine._load_module("assembling_court_binders")
        real_stream, real_overlay = assembler.folio_stream, assembler.folio_overlay_pdf
        folder = self.workspace / "badfolio"
        folder.mkdir()
        _make_filing_pdf(folder, "Tab01_Notice_15Nov2026.pdf", "BAD-FOLIO")
        with mock.patch.object(assembler, "folio_stream", lambda f, b, r: real_stream(f, b, r).replace("15 Tf", "10 Tf")), \
                mock.patch.object(assembler, "folio_overlay_pdf", lambda c: real_overlay(c, "Helvetica")):
            result = engine.assemble(folder, self.workspace / "bad_folio.pdf")
        failing = self._failing(engine.validate(Path(result["output_pdf"])))
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

    def test_api_sample_cycle_uses_the_folders_chosen_on_that_screen(self) -> None:
        """The sample screen's own pickers override the sidebar folders for one run."""
        with tempfile.TemporaryDirectory() as tmp:
            work, out = Path(tmp) / "my filings", Path(tmp) / "my binders"
            result = Api().run_full_cycle(str(work), str(out))
            self.assertTrue(result["ok"], result)
            self.assertTrue(Path(result["run_dir"]).is_relative_to(work))
            self.assertTrue(Path(result["assembled"]["output_pdf"]).is_relative_to(out))
            self.assertEqual(result["validation"]["passed_count"], 20)

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

    def test_building_without_any_details_still_works_and_names_the_placeholders(self) -> None:
        """Title page details are optional: a build with none succeeds and warns about what is missing."""
        with tempfile.TemporaryDirectory() as tmp:
            filings = Path(tmp) / "filings"
            filings.mkdir()
            _make_filing_pdf(filings, "Tab01_Notice_15Nov2026.pdf", "NO-DETAILS-FORM")
            blank = {"court": "Supreme Court of British Columbia", **{f: "" for f in engine.read_case_details(filings) if f not in ("court", "has_manifest", "has_cover_file")}}
            result = Api().assemble(str(filings), "Binder", str(Path(tmp) / "out"), blank)
            self.assertTrue(result["ok"], result)
            self.assertFalse((filings / "manifest.json").exists())
            self.assertTrue(any("court file number" in w for w in result["warnings"]), result["warnings"])
            self.assertNotIn("S-240123", _binder_text(Path(result["output_pdf"])))

    def test_partial_details_are_saved_and_only_missing_ones_flagged(self) -> None:
        """Entering only the file number saves it and warns only about the registry."""
        with tempfile.TemporaryDirectory() as tmp:
            filings = Path(tmp) / "filings"
            filings.mkdir()
            _make_filing_pdf(filings, "Tab01_Notice_15Nov2026.pdf", "PARTIAL")
            details = {"court": "Supreme Court of British Columbia", "file_number": "S-4242"}
            result = Api().assemble(str(filings), "Binder", str(Path(tmp) / "out"), details)
            self.assertTrue(result["ok"], result)
            self.assertIn("S-4242", _binder_text(Path(result["output_pdf"])))
            self.assertTrue(any("registry" in w and "court file number" not in w for w in result["warnings"]), result["warnings"])

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

    def test_custom_cover_page_needs_only_header_details_and_is_used(self) -> None:
        """With a custom cover file, only court/registry/file number are required and the cover text is printed."""
        with tempfile.TemporaryDirectory() as tmp:
            filings = Path(tmp) / "filings"
            filings.mkdir()
            _make_filing_pdf(filings, "Tab01_Notice_15Nov2026.pdf", "COVER-TEST")
            (filings / "000_Application_Record_Title_Page.txt").write_text("MY OWN COVER PAGE TEXT\nFor the hearing")
            self.assertTrue(engine.read_case_details(filings)["has_cover_file"])
            self.assertTrue(engine.inspect_folder(filings)["has_cover_file"])
            minimal = {"court": "Supreme Court of British Columbia", "registry": "Kelowna", "file_number": "S-1"}
            result = Api().assemble(str(filings), "Binder", str(Path(tmp) / "out"), minimal)
            self.assertTrue(result["ok"], result)
            self.assertIn("MY OWN COVER PAGE TEXT", _binder_text(Path(result["output_pdf"])))

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


class Gate18AndStrictTest(unittest.TestCase):
    """Tests for the exhibit bookmark rule and --strict."""

    FULL = CaseDetailsTest.FULL

    def _build(self, tmp: str, lines: list[str]) -> Path:
        """Builds a one-filing binder whose text is lines and returns its path."""
        filings = Path(tmp) / "filings"
        filings.mkdir()
        generator = engine._load_module("generating_court_documents")
        page = {"header": "AFFIDAVIT", "subtitle": "Affidavit #1 of Jane Roe", "lines": lines}
        (filings / "Tab01_Affidavit_1_Jane_Roe_15Nov2026.pdf").write_bytes(generator.create_multipage_pdf([page]))
        result = Api().assemble(str(filings), "Binder", str(Path(tmp) / "out"), self.FULL)
        self.assertTrue(result["ok"], result)
        return Path(result["output_pdf"])

    def _rule18(self, pdf: Path) -> dict:
        """Returns the RULE-18 check for pdf."""
        return next(c for c in engine.validate(pdf)["checks"] if c["rule"] == "RULE-18")

    def test_binder_without_exhibits_is_not_penalised(self) -> None:
        """No exhibit stamps means no exhibit bookmarks are required."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf = self._build(tmp, ["I, Jane Roe, swear that the facts below are true and within my knowledge. " * 2] * 3)
            check = self._rule18(pdf)
            self.assertTrue(check["passed"], check["details"])

    def test_exhibit_stamp_without_bookmark_is_flagged(self) -> None:
        """An exhibit stamp in the text with no exhibit bookmark must fail the gate."""
        with tempfile.TemporaryDirectory() as tmp:
            lines = ['This is Exhibit "A" referred to in the affidavit of Jane Roe sworn on March 3, 2027.'] + ["Further text of the affidavit goes here for the record. " * 2] * 3
            built = self._build(tmp, lines)
            writer = pypdf.PdfWriter()  # copy only the pages: a binder made elsewhere with no bookmarks
            for page in pypdf.PdfReader(str(built)).pages:
                writer.add_page(page)
            stripped = Path(tmp) / "no_bookmarks.pdf"
            writer.write(str(stripped))
            check = self._rule18(stripped)
            self.assertFalse(check["passed"])
            self.assertIn("Exhibit stamps", check["details"])

    def test_strict_flag_fails_on_soft_warnings(self) -> None:
        """--strict must exit non-zero when a SOFT_WARNING exists, while the default exits zero."""
        pdf = Path(__file__).resolve().parents[2] / "output" / "02-amendment" / "Application_Record.pdf"
        if not pdf.is_file():
            self.skipTest("sample output not present")
        script = engine.locate_scripts_dir() / "validating_court_binders.py"
        failing = [c for c in engine.validate(pdf)["checks"] if not c["passed"]]
        if not any(c["severity"] == "SOFT_WARNING" for c in failing):
            self.skipTest("sample has no soft warnings")
        normal = subprocess.run([sys.executable, str(script), "--file", str(pdf), "--json"], capture_output=True, text=True)
        strict = subprocess.run([sys.executable, str(script), "--file", str(pdf), "--json", "--strict"], capture_output=True, text=True)
        self.assertEqual(normal.returncode, 0)
        self.assertEqual(strict.returncode, 1)


class EncodingAndExhibitTest(unittest.TestCase):
    """Tests for non-ASCII text and automatic exhibit bookmarks."""

    FULL = CaseDetailsTest.FULL

    def _build_from_text(self, tmp: str, text: str) -> tuple[dict, Path]:
        """Builds a one-filing binder from text and returns the API result and the PDF path."""
        filings = Path(tmp) / "filings"
        filings.mkdir()
        doc = {"item_num": 1, "title": "Tab 1 - Affidavit", "short_title": "Affidavit #1 of Jane Roe",
               "filename": "Tab01_Affidavit.pdf", "exhibits": []}
        (filings / "manifest.json").write_text(json.dumps({"documents": [doc]}))
        (filings / "Tab01_Affidavit.txt").write_text(text, encoding="utf-8")
        result = Api().assemble(str(filings), "Binder", str(Path(tmp) / "out"), self.FULL)
        self.assertTrue(result["ok"], result)
        return result, Path(result["output_pdf"])

    def test_accents_dashes_and_curly_quotes_render_correctly(self) -> None:
        """Western European text must survive intact, not become mojibake."""
        with tempfile.TemporaryDirectory() as tmp:
            text = "Françoise Côté swore \u201cI agree\u201d \u2014 see the café agreement. " * 6
            _, pdf = self._build_from_text(tmp, text)
            out = _binder_text(pdf)
            self.assertIn("Françoise Côté", out)
            self.assertIn("\u201cI agree\u201d", out)
            self.assertNotIn("â€", out)

    def test_unsupported_characters_are_reported_not_silently_lost(self) -> None:
        """Characters the font cannot show produce a warning naming them."""
        with tempfile.TemporaryDirectory() as tmp:
            result, _ = self._build_from_text(tmp, "Plain English sentence for the filing record. " * 8 + "Łódź")
            self.assertTrue(any("Ł" in w for w in result["warnings"]), result["warnings"])

    def test_exhibits_are_bookmarked_from_their_stamps_without_a_manifest_list(self) -> None:
        """An exhibit stamp creates an Exhibit bookmark automatically."""
        with tempfile.TemporaryDirectory() as tmp:
            body = ["The deponent states the following facts under oath for this application. " * 2] * 30
            exhibit = ['EXHIBIT \u201cA\u201d - JOINT VENTURE AGREEMENT (PAGE 1 OF 1)',
                       'Commissioner Stamp: This is Exhibit \u201cA\u201d referred to in Affidavit #1 of Jane Roe.',
                       "Agreement text follows here and continues for the record of the court. " * 2]
            _, pdf = self._build_from_text(tmp, "\n".join(body + exhibit))
            titles = []
            reader = pypdf.PdfReader(str(pdf))
            stack = list(reader.outline)
            while stack:
                item = stack.pop(0)
                stack = (item if isinstance(item, list) else []) + stack
                if not isinstance(item, list):
                    titles.append(str(item.title))
            self.assertTrue(any("Exhibit A" in t and "Joint Venture Agreement" in t for t in titles), titles)
            check = next(c for c in engine.validate(pdf)["checks"] if c["rule"] == "RULE-18")
            self.assertTrue(check["passed"], check["details"])


class TrueCopyTest(unittest.TestCase):
    """Tests for true copies, nested bookmarks and the multi-page index."""

    def _pdf(self, folder: Path, name: str, marker: str, size=(612, 792), rotate: int = 0, pages: int = 1) -> None:
        """Writes a text PDF of the given size and rotation (via pypdf) into folder."""
        generator = engine._load_module("generating_court_documents")
        source = pypdf.PdfReader(__import__("io").BytesIO(generator.create_multipage_pdf(
            [{"header": f"{marker} {n}", "subtitle": "s", "lines": [f"{marker} line " * 6] * 4} for n in range(1, pages + 1)])))
        writer = pypdf.PdfWriter()
        for page in source.pages:
            page.mediabox = pypdf.generic.RectangleObject([0, 0, size[0], size[1]])
            if rotate:
                page.rotate(rotate)
            writer.add_page(page)
        with (folder / name).open("wb") as fh:
            writer.write(fh)

    def _build(self, tmp: str, files: int = 1, **kwargs) -> Path:
        """Builds a binder from `files` generated PDFs and returns its path."""
        folder = Path(tmp) / "in"
        folder.mkdir()
        for n in range(1, files + 1):
            self._pdf(folder, f"Tab{n:02d}_Notice_{n}_15Nov2026.pdf", f"ORIGINAL-{n}", **kwargs)
        result = Api().assemble(str(folder), "Binder", str(Path(tmp) / "out"))
        self.assertTrue(result["ok"], result)
        return Path(result["output_pdf"])

    def test_original_pages_are_kept_with_their_own_size_and_text(self) -> None:
        """A4 originals stay A4 and keep their text; the folio is added on top."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf = self._build(tmp, size=(595, 842))
            page = pypdf.PdfReader(str(pdf)).pages[2]
            self.assertEqual([round(float(x)) for x in page.mediabox], [0, 0, 595, 842])
            text = page.extract_text()
            self.assertIn("ORIGINAL-1", text)
            self.assertTrue(text.strip().endswith("1"), text[-20:])

    def test_rotated_originals_keep_rotation_and_get_an_upright_folio(self) -> None:
        """A landscape (rotated) page keeps its rotation and still carries the folio."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf = self._build(tmp, rotate=90)
            page = pypdf.PdfReader(str(pdf)).pages[2]
            self.assertEqual(int(page.rotation), 90)
            self.assertIn("ORIGINAL-1", page.extract_text())

    def test_folio_is_found_top_centre_in_every_orientation(self) -> None:
        """Portrait, landscape, A4 and pages rotated 90/180/270 all pass the folio gates."""
        cases = {
            "portrait": dict(),
            "landscape": dict(size=(792, 612)),
            "a4": dict(size=(595, 842)),
            "rotated 90": dict(rotate=90),
            "rotated 180": dict(rotate=180),
            "rotated 270": dict(rotate=270),
        }
        for label, kwargs in cases.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as tmp:
                pdf = self._build(tmp, **kwargs)
                checks = {c["rule"]: c for c in engine.validate(pdf)["checks"]}
                for rule in ("RULE-10", "RULE-11", "RULE-12", "RULE-13", "RULE-14"):
                    self.assertTrue(checks[rule]["passed"], (label, rule, checks[rule]["details"]))

    def test_binder_text_is_not_typeset_again(self) -> None:
        """With originals, the typesetting warning must not appear and all pages come from the source."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "in"
            folder.mkdir()
            self._pdf(folder, "Tab01_Notice_15Nov2026.pdf", "TRUE-COPY", pages=3)
            result = Api().assemble(str(folder), "Binder", str(Path(tmp) / "out"))
            self.assertFalse(any("typeset again" in w for w in result["warnings"]), result["warnings"])
            self.assertEqual(len(pypdf.PdfReader(result["output_pdf"]).pages), 2 + 3)

    def test_long_index_spills_onto_more_pages_and_links_stay_correct(self) -> None:
        """40 filings need more than one index page; every link must land on its filing's first page."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf = self._build(tmp, files=40)
            reader = pypdf.PdfReader(str(pdf))
            labels = reader.trailer["/Root"]["/PageLabels"]["/Nums"]
            front = int(labels[2])
            self.assertGreater(front, 2, "expected the index to need more than one page")
            self.assertEqual(len(reader.pages), front + 40)
            targets = []
            for index_page in reader.pages[1:front]:
                for annot in index_page.get("/Annots") or []:
                    targets.append(reader.get_page_number(annot.get_object()["/Dest"][0].get_object()))
            self.assertEqual(sorted(targets), list(range(front, front + 40)))
            checks = {c["rule"]: c for c in engine.validate(pdf)["checks"]}
            for rule in ("RULE-04", "RULE-05", "RULE-07", "RULE-10", "RULE-14"):
                self.assertTrue(checks[rule]["passed"], (rule, checks[rule]["details"]))

    def test_exhibit_on_a_documents_first_page_is_a_child_not_a_replacement(self) -> None:
        """An exhibit starting on page 1 keeps the document's own bookmark and nests beneath it."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "in"
            folder.mkdir()
            generator = engine._load_module("generating_court_documents")
            page = {"header": "AFFIDAVIT", "subtitle": "s", "lines": [
                'This is Exhibit "A" referred to in the affidavit of Jane Roe.', "Body text of the affidavit. " * 3]}
            (folder / "Tab01_Affidavit_1_Jane_Roe_15Nov2026.pdf").write_bytes(generator.create_multipage_pdf([page]))
            result = Api().assemble(str(folder), "Binder", str(Path(tmp) / "out"))
            outline = pypdf.PdfReader(result["output_pdf"]).outline
            titles = [(i.title if not isinstance(i, list) else [c.title for c in i]) for i in outline]
            self.assertTrue(any("Affidavit" in t for t in titles if isinstance(t, str)), titles)
            self.assertTrue(any(isinstance(t, list) and any("Exhibit A" in c for c in t) for t in titles), titles)


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
