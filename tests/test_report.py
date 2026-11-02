"""Report regression checks use synthetic data only."""

from copy import deepcopy
from html.parser import HTMLParser
import unittest

from kodewaspada.report import render_html, render_markdown


def example_report():
    return {
        "schema_version": 1,
        "tool": {"name": "KodeWaspada", "version": "0.1.0", "engine": "Semgrep CE", "engine_version": "test"},
        "project": {"name": "toko-contoh"},
        "created_at": "2026-11-02T12:00:00+00:00",
        "status": "completed",
        "coverage": {"discovered_files": 7, "scanned_files": 5, "rule_count": 3,
                     "skipped": [{"path": "assets/logo.png", "reason": "Format tidak didukung"}, {"path": "vendor.js", "reason": "Dikecualikan"}], "errors": []},
        "findings": [{
            "id": "demo-001", "rule_id": "request-to-command", "title": "Input request mencapai perintah shell",
            "priority": "tinggi", "status": "needs_review", "path": "src/server.ts", "line": 12, "end_line": 14,
            "source_line": 8, "explanation": "Analisis menunjukkan jalur input ke operasi sensitif.",
            "impact": "Jika input dapat dikendalikan, perintah yang tidak dimaksud dapat dijalankan.",
            "fix": "Hindari shell; gunakan API terstruktur dan allowlist argumen.",
            "verify": "Tambahkan tes yang menolak argumen di luar allowlist.",
            "ai_prompt": "Telusuri alur ini, periksa validasi, lalu usulkan perubahan dan uji regresi.",
            "references": ["https://owasp.org/www-community/attacks/Command_Injection"],
            "limitation": "Belum memverifikasi perilaku runtime atau alur lintas fungsi.",
        }],
    }


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.report = example_report()

    def test_readable_complete_report(self):
        html = render_html(self.report)
        markdown = render_markdown(self.report)
        for rendered in (html, markdown):
            self.assertIn("1 kandidat perlu ditinjau manusia", rendered)
            self.assertIn("src/server", rendered)
            self.assertIn("Perbaikan yang disarankan", rendered)
            self.assertIn("Cara menguji ulang", rendered)
            self.assertIn("Prompt untuk asisten AI", rendered)
            self.assertIn("bukan sertifikasi", rendered)
            self.assertIn("otorisasi/IDOR", rendered)
            self.assertIn("secrets belum diperiksa", rendered)
        self.assertIn("toko-contoh", html)
        self.assertIn("toko\\-contoh", markdown)
        self.assertIn("<dd>7</dd>", html)
        self.assertIn("<dd>5</dd>", html)
        self.assertIn("<dd>3</dd>", html)
        self.assertIn("<dd>2</dd>", html)
        self.assertIn("Baris 8", html)
        self.assertIn("Baris 12", html)
        self.assertIn("12–14", html)

    def test_html_escapes_all_dynamic_text(self):
        hostile = '\"><script>alert(1)</script><img src=x onerror=alert(2)>'
        for key in ("id", "rule_id", "title", "priority", "path", "explanation", "impact", "fix", "verify", "ai_prompt", "limitation"):
            self.report["findings"][0][key] = hostile
        self.report["project"]["name"] = hostile
        self.report["tool"]["version"] = hostile
        self.report["tool"]["engine"] = hostile
        self.report["tool"]["engine_version"] = hostile
        self.report["created_at"] = hostile
        self.report["coverage"]["skipped"] = [{"path": hostile, "reason": hostile}]
        self.report["coverage"]["errors"] = [{"path": hostile, "type": hostile, "message": hostile}]
        html = render_html(self.report)
        self.assertNotIn(hostile, html)
        self.assertIn("&lt;script&gt;", html)
        elements = Elements(html).elements
        self.assertFalse(any(tag in {"script", "img", "iframe", "object", "embed", "form"} for tag, _ in elements))
        self.assertFalse(any(key.startswith("on") for _, attrs in elements for key in attrs))

    def test_only_https_reference_links_are_rendered(self):
        self.report["findings"][0]["references"] = [
            "javascript:alert(1)", "data:text/html,boom", "http://example.org", "//example.org", "file:///tmp/a",
            "https://user:pass@example.org", "https://example.org:bad/", "https://[broken/", "https://example.org\\evil",
            "https://example.org/\npath", " https://example.org", None,
            "https://example.org/path?q=(safe)&v=1",
        ]
        html = render_html(self.report)
        links = [attrs["href"] for tag, attrs in Elements(html).elements if tag == "a" and not attrs["href"].startswith("#")]
        self.assertEqual(links, ["https://example.org/path?q=%28safe%29&v=1"])
        markdown = render_markdown(self.report)
        self.assertIn("https://example.org/path?q=%28safe%29&v=1", markdown)
        for scheme in ("javascript:", "data:", "file:", "http:"):
            self.assertNotIn(scheme, markdown)

    def test_markdown_cannot_inject_markup_or_structure(self):
        hostile = '# title\n<script>alert(1)</script>\n[x](javascript:boom)\n```\n![p](https://example.org)'
        self.report["project"]["name"] = hostile
        self.report["findings"][0]["path"] = hostile
        self.report["findings"][0]["ai_prompt"] = hostile
        markdown = render_markdown(self.report)
        self.assertNotIn("<script>", markdown)
        self.assertNotIn("\n# title", markdown)
        self.assertNotIn("[x](javascript:", markdown)
        self.assertNotIn("![p](https:", markdown)
        self.assertNotIn("```", markdown)
        self.assertIn("&lt;script&gt;", markdown)

    def test_empty_result_never_means_safe(self):
        self.report["findings"] = []
        for renderer in (render_html, render_markdown):
            rendered = renderer(self.report)
            self.assertIn("Tidak ada kandidat pada cakupan ini", rendered)
            self.assertIn("bukan jaminan aman", rendered)
            self.assertNotIn("0 kandidat perlu", rendered)

    def test_failed_and_partial_are_not_clean_results(self):
        self.report["findings"] = []
        for status, expected in (("failed", "Belum ada kesimpulan"), ("partial", "Hasil ini belum lengkap")):
            self.report["status"] = status
            self.report["coverage"]["errors"] = [{"type": "parse", "message": "File tidak dapat dibaca", "path": "src/a.ts"}]
            for renderer in (render_html, render_markdown):
                with self.subTest(status=status, renderer=renderer.__name__):
                    rendered = renderer(self.report)
                    self.assertIn(expected, rendered)
                    self.assertIn("File tidak dapat dibaca", rendered)
                    self.assertNotIn("Tidak ada kandidat pada cakupan ini", rendered)

    def test_unknown_source_is_explicit_and_no_code_is_leaked(self):
        self.report["findings"][0]["source_line"] = None
        self.report["findings"][0]["code"] = "SYNTHETIC_SECRET_DO_NOT_RENDER"
        self.report["raw_output"] = "SYNTHETIC_SECRET_DO_NOT_RENDER"
        for renderer in (render_html, render_markdown):
            rendered = renderer(self.report)
            self.assertIn("Lokasi asal input belum tersedia", rendered)
            self.assertNotIn("SYNTHETIC_SECRET_DO_NOT_RENDER", rendered)

    def test_navigation_anchors_exist_and_no_remote_assets(self):
        html = render_html(self.report)
        elements = Elements(html).elements
        ids = [attrs["id"] for _, attrs in elements if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        for tag, attrs in elements:
            if tag == "a" and attrs.get("href", "").startswith("#"):
                self.assertIn(attrs["href"][1:], ids)
            self.assertNotIn("src", attrs)
        self.assertIn("@media print", html)
        self.assertIn("Content-Security-Policy", html)
        self.assertIn('lang="id"', html)
        self.assertNotIn("<button", html)

    def test_summary_groups_rules_without_hiding_individual_findings(self):
        template = self.report["findings"][0]
        self.report["findings"] = [
            {**template, "id": f"demo-{number}", "rule_id": f"rule-{number % 3}", "line": number + 1, "end_line": number + 1}
            for number in range(20)
        ]
        html = render_html(self.report)
        summary = html.split('<ol class="jump-list"', 1)[1].split("</ol>", 1)[0]
        self.assertEqual(summary.count("<li>"), 3)
        self.assertEqual(summary.count("7 kandidat"), 2)
        self.assertEqual(summary.count("6 kandidat"), 1)
        self.assertIn('href="#kandidat-1"', summary)
        self.assertIn('href="#kandidat-2"', summary)
        self.assertIn('href="#kandidat-3"', summary)
        self.assertEqual(html.count('<article class="finding"'), 20)
        self.assertIn("20 kandidat perlu ditinjau manusia", html)
        self.assertIn('id="kandidat-20"', html)

    def test_skipped_entries_include_files_and_directories(self):
        self.report["coverage"]["skipped"].append({"path": "node_modules/", "reason": "Folder dikecualikan"})
        for renderer in (render_html, render_markdown):
            rendered = renderer(self.report)
            self.assertIn("Entri dilewati", rendered)
            self.assertIn("Berkas/folder yang dilewati", rendered)
            self.assertNotIn("File dilewati", rendered)

    def test_truncated_skipped_count_is_labeled_as_displayed_only(self):
        self.report["coverage"]["skipped"].append({"path": "src/a.mts", "reason": "Belum didukung"})
        self.report["coverage"]["errors"].append({"type": "diagnostic_limit", "message": "Dibatasi"})
        for renderer in (render_html, render_markdown):
            self.assertIn("Entri dilewati ditampilkan", renderer(self.report))

    def test_render_does_not_mutate_report(self):
        before = deepcopy(self.report)
        render_html(self.report)
        render_markdown(self.report)
        self.assertEqual(self.report, before)


if __name__ == "__main__":
    unittest.main()
