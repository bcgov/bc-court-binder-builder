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

import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
