"""Exercise real Semgrep parsing/taint on synthetic, never-executed code."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "kodewaspada" / "rules" / "javascript.json"
GUIDANCE = RULES.with_name("guidance.json")
RULE_IDS = {"kw-request-shell", "kw-request-eval", "kw-request-html"}


class RuleContractTests(unittest.TestCase):
    def test_rules_are_local_original_taint_rules(self):
        rules = json.loads(RULES.read_text(encoding="utf-8"))["rules"]
        self.assertEqual({rule["id"] for rule in rules}, RULE_IDS)
        self.assertEqual(len(rules), 3)
        for rule in rules:
            self.assertEqual(rule["mode"], "taint")
            self.assertTrue(rule["pattern-sources"])
            self.assertTrue(rule["pattern-sinks"])
            self.assertEqual(rule["metadata"]["validation"], "candidate")

    def test_every_rule_has_plain_language_guidance(self):
        guidance = json.loads(GUIDANCE.read_text(encoding="utf-8"))
        self.assertEqual(set(guidance), RULE_IDS)
        for entry in guidance.values():
            for field in ("title", "priority", "explanation", "impact", "fix", "verify", "ai_prompt", "limitation"):
                self.assertIsInstance(entry[field], str)
                self.assertTrue(entry[field].strip())
            self.assertIn(entry["priority"], {"tinggi", "sedang"})
            self.assertTrue(entry["references"])
            self.assertTrue(all(link.startswith("https://") for link in entry["references"]))


@unittest.skipUnless(shutil.which("semgrep"), "Semgrep belum terpasang; jalankan instalasi sesuai README sebelum rilis")
class SemgrepRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        completed = subprocess.run(
            ["semgrep", "scan", "--config", str(RULES), "--json", "--metrics", "off",
             "--disable-version-check", "--oss-only", "--no-git-ignore", "--disable-nosem",
             "--no-rewrite-rule-ids", "examples"],
            cwd=ROOT, capture_output=True, text=True, timeout=90,
            env={**os.environ, "SEMGREP_SEND_METRICS": "off", "SEMGREP_ENABLE_VERSION_CHECK": "0"},
        )
        if completed.returncode:
            raise AssertionError(f"Semgrep gagal ({completed.returncode}): {completed.stderr}")
        cls.report = json.loads(completed.stdout)
        cls.matches = {
            (match["path"], match["start"]["line"], match["check_id"])
            for match in cls.report["results"]
        }
        cls.positive, cls.negative = set(), set()
        for path in sorted((ROOT / "examples").rglob("*")):
            if path.suffix not in {".js", ".ts", ".jsx", ".tsx"}:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                annotation = re.search(r"// (ruleid|ok): (kw-request-[a-z]+)$", line)
                if annotation:
                    expected = (str(path.relative_to(ROOT)), number + 1, annotation[2])
                    (cls.positive if annotation[1] == "ruleid" else cls.negative).add(expected)

    def test_no_parser_or_rule_errors(self):
        self.assertEqual(self.report["errors"], [])
        self.assertEqual(self.report.get("skipped_rules", []), [])

    def test_every_expected_flow_is_found(self):
        self.assertTrue(self.positive)
        self.assertEqual(self.positive - self.matches, set())

    def test_controls_do_not_match(self):
        self.assertTrue(self.negative)
        self.assertEqual(self.negative & self.matches, set())

    def test_no_unexpected_findings(self):
        self.assertEqual(self.matches - self.positive, set())

    def test_javascript_and_typescript_are_exercised(self):
        paths = self.report["paths"]["scanned"]
        self.assertTrue(any(path.endswith(".js") for path in paths))
        self.assertTrue(any(path.endswith(".tsx") for path in paths))
        self.assertEqual({rule for _, _, rule in self.matches}, RULE_IDS)


if __name__ == "__main__":
    unittest.main()
