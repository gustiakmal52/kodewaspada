import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from kodewaspada import scanner


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "input"
        self.stage = Path(self.temporary.name) / "stage"
        self.root.mkdir()
        self.stage.mkdir()

    def put(self, name, content=b"const answer = 42;"):
        file = self.root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
        return file

    def test_supported_files_copied_exactly_without_running(self):
        source = self.put("src/main.ts", b"throw new Error('must never execute');")
        included, skipped, errors, count = scanner._stage(self.root, self.stage)
        self.assertEqual(included, ["src/main.ts"])
        self.assertEqual((count, skipped, errors), (1, [], []))
        self.assertEqual(source.read_bytes(), (self.stage / "src/main.ts").read_bytes())

    def test_secrets_dependencies_and_git_are_not_staged(self):
        for name in [".env", ".env.js", ".git/config.js", "node_modules/secret.js", "outputs/report.js", "document.pdf"]:
            self.put(name, b"FAKE_PRIVATE_TEST_MARKER")
        included, skipped, errors, _ = scanner._stage(self.root, self.stage)
        self.assertEqual(included, [])
        self.assertFalse(errors)
        self.assertGreaterEqual(len(skipped), 4)

    def test_file_and_directory_symlinks_are_not_followed(self):
        external = Path(self.temporary.name) / "external"
        external.mkdir()
        (external / "private.js").write_text("SYNTHETIC_PRIVATE_MARKER")
        (self.root / "linked.js").symlink_to(external / "private.js")
        (self.root / "linked_dir").symlink_to(external, target_is_directory=True)
        included, skipped, _, _ = scanner._stage(self.root, self.stage)
        self.assertEqual(included, [])
        self.assertEqual(len(skipped), 2)

    def test_oversized_binary_and_invalid_utf8_are_partial(self):
        self.put("large.js", b"a" * (scanner.MAX_FILE_BYTES + 1))
        self.put("binary.ts", b"zero\0byte")
        self.put("encoding.js", b"\xff")
        included, skipped, errors, _ = scanner._stage(self.root, self.stage)
        self.assertEqual(included, [])
        self.assertEqual(len(errors), 3)
        self.assertEqual(len(skipped), 3)

    def test_file_limit_reports_incomplete(self):
        self.put("a.js")
        self.put("b.js")
        with patch.object(scanner, "MAX_FILES", 1):
            included, _, errors, _ = scanner._stage(self.root, self.stage)
        self.assertEqual(len(included), 1)
        self.assertEqual(errors[0]["type"], "file_limit")

    def test_total_byte_limit_reports_incomplete(self):
        self.put("a.js", b"a" * 4)
        self.put("b.js", b"b" * 4)
        with patch.object(scanner, "MAX_TOTAL_BYTES", 6):
            included, _, errors, _ = scanner._stage(self.root, self.stage)
        self.assertEqual(len(included), 1)
        self.assertEqual(errors[0]["type"], "size_limit")

    def test_entry_limit_reports_incomplete(self):
        self.put("a.txt")
        self.put("b.txt")
        with patch.object(scanner, "MAX_ENTRIES", 1):
            _, _, errors, _ = scanner._stage(self.root, self.stage)
        self.assertEqual(errors[0]["type"], "entry_limit")

    def test_control_characters_cannot_escape_terminal(self):
        name = "evil\x1b[31m\n\u202e.js"
        self.assertNotIn("\x1b", scanner.display_path(name))
        self.assertNotIn("\n", scanner.display_path(name))
        self.assertNotIn("\u202e", scanner.display_path(name))

    def test_mts_and_cts_are_reported_as_unsupported(self):
        self.put("source.mts")
        self.put("source.cts")
        included, skipped, errors, count = scanner._stage(self.root, self.stage)
        self.assertEqual(included, [])
        self.assertEqual(count, 2)
        self.assertEqual(len(skipped), 2)
        self.assertTrue(all(e["type"] == "unsupported_extension" for e in errors))

    def test_diagnostic_limit_does_not_block_supported_sources(self):
        for number in range(8):
            self.put(f"unsupported-{number}.mts")
        self.put("supported.js")
        with patch.object(scanner, "MAX_DIAGNOSTIC_ITEMS", 3):
            included, skipped, errors, count = scanner._stage(self.root, self.stage)
        self.assertIn("supported.js", included)
        self.assertEqual(count, 9)
        self.assertLessEqual(len(skipped) + len(errors), 3)
        limits = [item for item in errors if item["type"] == "diagnostic_limit"]
        self.assertEqual(limits, [scanner._DIAGNOSTIC_LIMIT])
        self.assertNotIn("path", limits[0])

    def test_diagnostic_byte_limit_uses_fixed_sentinel(self):
        self.put(f"{'a' * 120}.mts")
        budget = scanner._json_bytes(scanner._DIAGNOSTIC_LIMIT) + 16
        with patch.object(scanner, "MAX_DIAGNOSTIC_BYTES", budget):
            _, skipped, errors, _ = scanner._stage(self.root, self.stage)
        retained = skipped + errors
        self.assertEqual(retained, [scanner._DIAGNOSTIC_LIMIT])
        self.assertLessEqual(sum(scanner._json_bytes(item) for item in retained), budget)


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        self.stage = Path("/tmp/example-stage/source")
        self.guide = {"kw-request-shell": {"title": "Input ke shell", "priority": "tinggi"}}
        self.result = {"check_id": "kw-request-shell", "path": str(self.stage / "index.js"),
                       "start": {"line": 2}, "end": {"line": 3},
                       "extra": {"lines": "SYNTHETIC_SECRET_DO_NOT_COPY", "metavars": {"key": "PRIVATE"}}}
        self.payload = {"results": [self.result], "errors": [], "paths": {"scanned": [str(self.stage / "index.js")]}}

    def normalize(self):
        return scanner.normalize(self.payload, self.stage, {"index.js"}, self.guide)

    def test_only_allowlisted_fields_reach_report(self):
        findings, errors, count = self.normalize()
        self.assertEqual(count, 1)
        self.assertFalse(errors)
        self.assertEqual(findings[0]["status"], "needs_review")
        self.assertEqual(findings[0]["path"], "index.js")
        self.assertNotIn("SYNTHETIC_SECRET", json.dumps(findings))
        self.assertNotIn("/tmp", json.dumps(findings))

    def test_unconfirmed_coverage_never_counts_complete(self):
        self.payload["paths"]["scanned"] = []
        _, errors, count = self.normalize()
        self.assertEqual(count, 0)
        self.assertEqual(errors[0]["type"], "coverage_gap")

    def test_raw_diagnostics_not_exposed(self):
        self.payload["errors"] = [{"message": "SYNTHETIC_SECRET", "path": "/private/source"}] * 50
        _, errors, _ = self.normalize()
        self.assertEqual(sum(error["type"] == "engine_diagnostic" for error in errors), 1)
        self.assertNotIn("SYNTHETIC_SECRET", json.dumps(errors))
        self.assertNotIn("/private", json.dumps(errors))

    def test_skipped_rules_are_not_reported_complete(self):
        self.payload["skipped_rules"] = [{"message": "SYNTHETIC_SECRET"}]
        _, errors, _ = self.normalize()
        self.assertEqual(errors[0]["type"], "skipped_rules")
        self.assertNotIn("SYNTHETIC_SECRET", json.dumps(errors))

    def test_unknown_rule_fails_closed(self):
        self.result["check_id"] = "injected-rule"
        with self.assertRaises(ValueError):
            self.normalize()

    def test_traversal_and_external_paths_fail_closed(self):
        for path in ("../index.js", "/etc/passwd", "unknown.js"):
            self.result["path"] = path
            with self.assertRaises(ValueError):
                self.normalize()

    def test_invalid_location_fails_closed(self):
        self.result["start"]["line"] = -3
        with self.assertRaises(ValueError):
            self.normalize()

    def test_duplicate_findings_deduplicated(self):
        self.payload["results"] *= 2
        self.assertEqual(len(self.normalize()[0]), 1)

    def test_finding_item_limit_marks_analysis_incomplete(self):
        self.payload["results"] = [
            {**self.result, "start": {"line": line}, "end": {"line": line}}
            for line in range(1, 5)
        ]
        with patch.object(scanner, "MAX_FINDING_ITEMS", 2):
            findings, errors, _ = self.normalize()
        self.assertEqual(len(findings), 2)
        self.assertEqual(errors[0]["type"], "finding_limit")

    def test_finding_byte_limit_marks_analysis_incomplete(self):
        with patch.object(scanner, "MAX_FINDING_BYTES", 1):
            findings, errors, _ = self.normalize()
        self.assertEqual(findings, [])
        self.assertEqual(errors[0]["type"], "finding_limit")

    def test_command_never_enables_cloud_or_target_execution(self):
        command = scanner.engine_command("/trusted/semgrep", self.stage)
        for flag in ("--metrics=off", "--disable-version-check", "--oss-only", "--disable-nosem", "--no-git-ignore"):
            self.assertIn(flag, command)
        self.assertNotIn("--autofix", command)
        self.assertNotIn("auto", command)
        self.assertNotIn("ci", command)


class ScanFailures(unittest.TestCase):
    def test_missing_engine_gives_actionable_error(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(scanner.shutil, "which", return_value=None):
            with self.assertRaisesRegex(ValueError, "Semgrep belum"):
                scanner.scan(folder)

    def test_missing_folder_rejected(self):
        with self.assertRaisesRegex(ValueError, "folder proyek"):
            scanner.scan("/nonexistent-kodewaspada-fixture")

    def test_engine_in_target_is_not_executed(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(scanner.shutil, "which", return_value=folder + "/semgrep"):
            with self.assertRaisesRegex(ValueError, "Engine di dalam"):
                scanner.scan(folder)

    def test_no_sources_is_failed_not_clean(self):
        with tempfile.TemporaryDirectory() as folder:
            report = scanner.scan(folder)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["coverage"]["errors"][0]["type"], "no_sources")
        self.assertGreaterEqual(report["tool"]["scan_duration_ms"], 0)

    def test_engine_failure_is_failed_not_clean(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "index.js").write_text("let x = 1;")
            with patch.object(scanner, "_run_engine", side_effect=RuntimeError("SYNTHETIC_SECRET")):
                report = scanner.scan(folder)
        self.assertEqual(report["status"], "failed")
        self.assertGreaterEqual(report["tool"]["scan_duration_ms"], 0)
        self.assertNotIn("SYNTHETIC_SECRET", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
