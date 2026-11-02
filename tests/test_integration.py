from pathlib import Path
import shutil
import tempfile
import unittest

from kodewaspada.scanner import scan


@unittest.skipUnless(shutil.which("semgrep"), "Semgrep diperlukan untuk uji end-to-end")
class EndToEndTests(unittest.TestCase):
    def scan_sources(self, files):
        with tempfile.TemporaryDirectory() as folder:
            for name, text in files.items():
                (Path(folder) / name).write_text(text, encoding="utf-8")
            return scan(folder)

    def test_actual_source_to_report_with_control(self):
        report = self.scan_sources({"route.js": "function route(req) { eval(req.query.code); }", "control.ts": "const result = JSON.parse('{}');"})
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["coverage"]["scanned_files"], 2)
        self.assertEqual(len(report["findings"]), 1)
        self.assertEqual(report["findings"][0]["rule_id"], "kw-request-eval")
        self.assertEqual(report["findings"][0]["status"], "needs_review")

    def test_unsupported_source_retains_partial_not_clean(self):
        report = self.scan_sources({"control.js": "const result = 1;", "ignored.mts": "function route(req) { eval(req.query.code); }"})
        self.assertEqual(report["status"], "partial")
        self.assertTrue(any(e["type"] == "unsupported_extension" for e in report["coverage"]["errors"]))
        self.assertEqual(report["coverage"]["scanned_files"], 1)

    def test_engine_parse_error_is_visible_as_incomplete(self):
        report = self.scan_sources({"broken.js": "function route(req) { eval(req.query.code); let = ; }"})
        self.assertNotEqual(report["status"], "completed")
        self.assertTrue(report["coverage"]["errors"])


if __name__ == "__main__":
    unittest.main()
