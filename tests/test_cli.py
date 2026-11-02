from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from kodewaspada.cli import main


def report(status="completed", findings=None):
    return {"schema_version": 1, "tool": {"name": "KodeWaspada", "version": "0.1.0", "engine": "Semgrep CE", "engine_version": "test"},
            "project": {"name": "synthetic"}, "created_at": "2026-11-02T00:00:00Z", "status": status,
            "coverage": {"discovered_files": 1, "scanned_files": 1, "rule_count": 3, "skipped": [], "errors": []},
            "findings": findings or []}


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "new-report"
        self.stdout, self.stderr = io.StringIO(), io.StringIO()

    def invoke(self):
        with redirect_stdout(self.stdout), redirect_stderr(self.stderr):
            return main(["scan", str(self.root), "--out", str(self.output)])

    def test_generates_all_three_formats_with_no_safe_claim(self):
        with patch("kodewaspada.cli.scan", return_value=report()):
            self.assertEqual(self.invoke(), 0)
        self.assertEqual({p.name for p in self.output.iterdir()}, {"report.html", "report.md", "report.json"})
        self.assertIn("bukan bukti aman", self.stdout.getvalue())
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)

    def test_failed_analysis_keeps_diagnostic_report_and_exit_two(self):
        with patch("kodewaspada.cli.scan", return_value=report("failed")):
            self.assertEqual(self.invoke(), 2)
        self.assertEqual(json.loads((self.output / "report.json").read_text())["status"], "failed")

    def test_partial_analysis_does_not_pass(self):
        with patch("kodewaspada.cli.scan", return_value=report("partial")):
            self.assertEqual(self.invoke(), 2)

    def test_formats_are_created_serially(self):
        expected = report()

        def html(value):
            self.assertEqual(json.loads((self.output / "report.json").read_text()), expected)
            return "HTML"

        def markdown(value):
            self.assertEqual((self.output / "report.html").read_text(), "HTML")
            return "MARKDOWN"

        with (patch("kodewaspada.cli.scan", return_value=expected),
              patch("kodewaspada.cli.render_html", side_effect=html),
              patch("kodewaspada.cli.render_markdown", side_effect=markdown)):
            self.assertEqual(self.invoke(), 0)
        self.assertEqual((self.output / "report.md").read_text(), "MARKDOWN")

    def test_truncated_diagnostics_remain_partial(self):
        truncated = report("partial")
        truncated["coverage"]["errors"] = [{"type": "diagnostic_limit", "message": "truncated"}]
        with patch("kodewaspada.cli.scan", return_value=truncated):
            self.assertEqual(self.invoke(), 2)
        self.assertTrue((self.output / "report.html").is_file())

    def test_existing_report_is_never_overwritten_or_scanned(self):
        self.output.mkdir()
        existing = self.output / "report.html"
        existing.write_text("KEEP_ORIGINAL")
        with patch("kodewaspada.cli.scan") as scan:
            with self.assertRaises(SystemExit) as caught:
                self.invoke()
        self.assertEqual(caught.exception.code, 2)
        scan.assert_not_called()
        self.assertEqual(existing.read_text(), "KEEP_ORIGINAL")

    def test_symbolic_output_is_rejected(self):
        self.output.symlink_to(self.root / "not-existing")
        with self.assertRaises(SystemExit) as caught:
            self.invoke()
        self.assertEqual(caught.exception.code, 2)

    def test_input_failure_does_not_create_success_artifacts(self):
        with patch("kodewaspada.cli.scan", side_effect=ValueError("Folder tidak valid")):
            self.assertEqual(self.invoke(), 2)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
