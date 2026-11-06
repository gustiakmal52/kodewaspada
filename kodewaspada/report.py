"""Offline reports: review guidance, never an assurance of application security."""

from html import escape
import re
from urllib.parse import quote, urlsplit


_STATUS = {
    "completed": "Pemeriksaan selesai",
    "partial": "Pemeriksaan belum lengkap",
    "failed": "Pemeriksaan gagal",
}
_LIMITS = (
    "Versi ini hanya memeriksa JavaScript/TypeScript dengan 3 aturan bawaan. "
    "Autentikasi, otorisasi/IDOR, kebijakan database/RLS, dependensi, dan "
    "kebocoran secrets belum diperiksa. Analisis statis tidak menjalankan aplikasi "
    "dan tidak membuktikan kerentanan saat runtime. Laporan ini bukan sertifikasi "
    "keamanan; hasil tanpa temuan bukan jaminan aman."
)
_CSS = """
:root{color-scheme:light;--paper:#f6f3eb;--ink:#252822;--muted:#62645c;--line:#d6d5cb;--accent:#a83e12}
*{box-sizing:border-box}html{scroll-padding-top:24px}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:var(--accent);text-underline-offset:4px;overflow-wrap:anywhere}a:hover{text-decoration-thickness:2px}a:focus-visible{outline:3px solid var(--accent);outline-offset:5px}
.skip{position:absolute;left:12px;top:-80px;background:var(--ink);color:white;padding:12px;z-index:2}.skip:focus{top:12px}
.page{max-width:1280px;margin:auto;padding:48px 40px 80px;display:grid;grid-template-columns:190px minmax(0,1fr);gap:64px}
.rail{align-self:start;position:sticky;top:40px}.brand{font-size:21px;font-weight:800;letter-spacing:-.7px}.brand span{color:var(--accent)}
.edition,.eyebrow,.finding-number{font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:1px;text-transform:uppercase}
.edition{color:var(--muted);margin:8px 0 40px}.rail nav{display:grid;gap:4px}.rail nav a{color:var(--ink);padding:10px 0;text-decoration:none;border-bottom:1px solid var(--line)}
.rail-note{margin-top:32px;font-size:13px;color:var(--muted)}main{min-width:0}.eyebrow{color:var(--accent);margin:0 0 20px}
h1,h2,h3{line-height:1.12;letter-spacing:-.035em;overflow-wrap:anywhere}h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:clamp(40px,5.5vw,68px);max-width:700px;margin:0 0 28px}
h2{font-size:29px;margin:0 0 20px}h3{font-size:24px;margin:10px 0 18px}h4{font-size:15px;margin:24px 0 6px}p{margin:0 0 14px}.project{font-size:20px;overflow-wrap:anywhere}.meta{font-size:13px;color:var(--muted);overflow-wrap:anywhere}
.verdict{border-left:4px solid var(--accent);padding:20px 24px;background:#eeeadf;margin-top:32px}.verdict strong{display:block;font-size:19px;margin-bottom:7px}.verdict p:last-child{margin:0}
section{margin-top:52px;padding-top:28px;border-top:1px solid var(--line)}.intro{color:var(--muted);max-width:70ch}.jump-list{list-style:none;margin:24px 0 0;padding:0}.jump-list li{border-top:1px solid var(--line);padding:16px 0}.jump-list a{color:var(--ink);font-weight:650}.priority{font-size:12px;color:var(--accent);text-transform:uppercase;letter-spacing:.6px;display:block;margin-bottom:4px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin:24px 0 28px}.stats div{border-top:2px solid var(--ink);padding-top:12px}.stats dt{font-size:13px;color:var(--muted)}.stats dd{margin:4px 0 0;font-size:30px;font-weight:650;line-height:1.2}
.list{padding-left:22px}.list li{margin:10px 0;overflow-wrap:anywhere}code{font:13px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere;white-space:pre-wrap}
.finding{margin-top:36px;padding-top:24px;border-top:1px solid var(--ink)}.finding-number{color:var(--accent)}.location{padding:12px 16px;border:1px solid var(--line);overflow-wrap:anywhere}.flow{padding:0;list-style:none;display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:18px 0}.flow li{padding:14px 16px;background:#eeeadf}.flow b{display:block;font-size:13px}.flow span{font-size:14px}
.finding p,.finding pre{overflow-wrap:anywhere}.prompt{white-space:pre-wrap;word-break:break-word;font:14px/1.7 ui-monospace,SFMono-Regular,Consolas,monospace;padding:18px;background:#eeeadf;border-left:2px solid var(--ink)}
.refs{padding-left:20px;font-size:14px}.refs li{margin-bottom:6px}.notice{font-size:14px;color:var(--muted)}footer{border-top:1px solid var(--line);margin-top:48px;padding-top:24px;color:var(--muted);font-size:13px}
@media(max-width:800px){.page{grid-template-columns:1fr;gap:32px;padding:24px 22px 48px}.rail{position:static}.edition{margin:4px 0 16px}.rail nav{display:flex;gap:20px;flex-wrap:wrap}.rail nav a{padding:8px 0}.rail-note{display:none}.stats{grid-template-columns:1fr 1fr}h1{font-size:44px}section{margin-top:36px}.flow{grid-template-columns:1fr}}
@media print{@page{margin:18mm}body{background:white;font-size:10pt}.page{display:block;padding:0;max-width:none}.rail,.skip,.jump-list,.print-help{display:none}h1{font-size:30pt}h2{font-size:20pt}h3{font-size:16pt}h1,h2,h3,h4{break-after:avoid}section,.finding{margin-top:24px;padding-top:18px}.verdict{background:transparent}.stats{grid-template-columns:repeat(4,1fr)}a{color:inherit}.flow li,.prompt{background:transparent;border:1px solid #ccc}.prompt{font-size:9pt;white-space:pre-wrap}footer{font-size:9pt}.meta,.notice{color:#444}}
"""


def _text(value: object) -> str:
    return escape(str(value), quote=True)


def _markdown(value: object) -> str:
    # Keep untrusted filenames and messages from introducing Markdown structure.
    text = " ".join(str(value).splitlines())
    return re.sub(r"([\\`*_{}\[\]()#+.!|~>-])", r"\\\1", escape(text, quote=False))


def _safe_reference(value: object) -> str | None:
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 for c in value):
        return None
    if any(c in value for c in '\\<>"'):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return None
        parsed.port  # Reject malformed or out-of-range ports as well.
    except ValueError:
        return None
    return quote(value, safe=":/?&=#%+~;,@$!*-._")


def _summary(report: dict) -> tuple[str, str]:
    status = report.get("status")
    count = len(report.get("findings", []))
    if status == "failed":
        return "Belum ada kesimpulan yang bisa diambil.", "Perbaiki kendala di bagian cakupan, lalu jalankan pemeriksaan ulang."
    if status != "completed":
        return "Hasil ini belum lengkap.", "Tinjau kandidat yang tersedia, lalu selesaikan kendala pemeriksaan. Bagian yang belum dipindai tidak boleh dianggap aman."
    if count:
        return f"{count} kandidat perlu ditinjau manusia.", "Mulai dari kandidat berprioritas tinggi. Lokasi kode adalah petunjuk analisis statis, bukan bukti serangan berhasil."
    return "Tidak ada kandidat pada cakupan ini.", "Ini bukan jaminan aman. Periksa cakupan, file yang dilewati, dan area yang belum didukung sebelum mengambil keputusan."


def _location(finding: dict) -> str:
    line = finding["line"]
    end = finding.get("end_line", line)
    return f"{finding['path']}:{line}" + (f"–{end}" if end != line else "")


def _finding_html(finding: dict, number: int) -> str:
    source = finding.get("source_line")
    flow = (
        '<ol class="flow" aria-label="Alur yang ditunjukkan analisis statis">'
        f'<li><b>1. Asal input</b><span>Baris {_text(source)}</span></li>'
        f'<li><b>2. Operasi sensitif</b><span>Baris {_text(finding["line"])}</span></li></ol>'
        if source is not None else
        '<p class="notice">Lokasi asal input belum tersedia; telusuri alurnya secara manual.</p>'
    )
    fields = "".join(
        f"<h4>{label}</h4><p>{_text(finding[key])}</p>"
        for key, label in (
            ("explanation", "Apa yang terbaca"),
            ("impact", "Mengapa perlu dicek"),
            ("fix", "Perbaikan yang disarankan"),
            ("verify", "Cara menguji ulang"),
            ("limitation", "Batas deteksi kandidat ini"),
        )
    )
    references = "".join(
        f'<li><a href="{_text(url)}" rel="noreferrer">{_text(url)}</a></li>'
        for value in finding.get("references", []) if (url := _safe_reference(value))
    )
    return f"""<article class="finding" id="kandidat-{number}" aria-labelledby="judul-{number}">
<div class="finding-number">Kandidat {number:02d} / prioritas {_text(finding['priority'])} / perlu ditinjau</div>
<h3 id="judul-{number}">{_text(finding['title'])}</h3>
<p class="location"><code>{_text(_location(finding))}</code></p>
<p class="meta">Aturan: <code>{_text(finding['rule_id'])}</code> · ID: <code>{_text(finding['id'])}</code></p>
{flow}{fields}
<h4>Prompt untuk asisten AI</h4>
<p class="notice">Salin bila diperlukan. Tinjau perubahan dan hasil uji; jangan kirim secrets atau kode privat ke layanan AI tanpa izin.</p>
<pre class="prompt">{_text(finding['ai_prompt'])}</pre>
{('<h4>Rujukan</h4><ul class="refs">' + references + '</ul>') if references else ''}
</article>"""


def render_html(report: dict) -> str:
    """Render the version-1 report schema without scripts, remote assets, or code snippets."""
    coverage = report["coverage"]
    findings = report.get("findings", [])
    diagnostics_truncated = any(item.get("type") == "diagnostic_limit" for item in coverage.get("errors", []))
    title, summary = _summary(report)
    status = _STATUS.get(report.get("status"), "Status pemeriksaan tidak dikenal")
    groups = {}
    for number, finding in enumerate(findings, 1):
        group = groups.setdefault(finding["rule_id"], {"first": number, "finding": finding, "count": 0})
        group["count"] += 1
    summaries = []
    for group in groups.values():
        finding = group["finding"]
        summaries.append(
            f'<li><span class="priority">{group["count"]} kandidat · prioritas {_text(finding["priority"])} · perlu ditinjau</span>'
            f'<a href="#kandidat-{group["first"]}">{_text(finding["title"])}</a>'
            f'<div class="notice">Lihat kandidat pertama dari aturan ini.</div></li>'
        )
    items = "".join(summaries)
    stats = "".join(
        f"<div><dt>{label}</dt><dd>{_text(value)}</dd></div>"
        for label, value in (
            ("File ditemukan", coverage["discovered_files"]),
            ("File dipindai", coverage["scanned_files"]),
            ("Aturan dalam cakupan", coverage["rule_count"]),
            (("Entri dilewati ditampilkan" if diagnostics_truncated else "Entri dilewati"), len(coverage.get("skipped", []))),
        )
    )
    skipped = "".join(
        f'<li><code>{_text(item["path"])}</code> — {_text(item["reason"])}</li>'
        for item in coverage.get("skipped", [])
    )
    errors = "".join(
        f'<li><strong>{_text(item["type"])}</strong>'
        + (f' · <code>{_text(item["path"])}</code>' if item.get("path") else "")
        + f': {_text(item["message"])}</li>'
        for item in coverage.get("errors", [])
    )
    detail = "".join(_finding_html(finding, number) for number, finding in enumerate(findings, 1))
    tool = report["tool"]
    duration = tool.get("scan_duration_ms")
    timing = f'<br>Waktu scanner: {_text(duration)} ms (sebelum penulisan laporan)' if type(duration) is int and duration >= 0 else ''
    return f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer">
<title>Laporan KodeWaspada — {_text(report['project']['name'])}</title><style>{_CSS}</style></head>
<body><a class="skip" href="#ringkasan">Lewati navigasi</a><div class="page">
<aside class="rail"><div class="brand">Kode<span>Waspada</span></div>
<p class="edition">Laporan lokal / {_text(tool['version'])}</p>
<nav aria-label="Bagian laporan"><a href="#ringkasan">01 — Ringkasan</a><a href="#cakupan">02 — Cakupan</a><a href="#kandidat">03 — Kandidat</a><a href="#berikutnya">04 — Langkah berikutnya</a></nav>
<p class="rail-note">Baca bukti.<br>Pahami dampak.<br>Uji perbaikannya.</p></aside>
<main id="ringkasan"><header><p class="eyebrow">Pemeriksaan kode / {_text(status)}</p>
<h1>Lihat risikonya.<br>Pahami langkah berikutnya.</h1>
<p class="project">Proyek: <strong>{_text(report['project']['name'])}</strong></p>
<p class="meta">Dibuat {_text(report['created_at'])}<br>Mesin: {_text(tool['engine'])} {_text(tool['engine_version'])}{timing}</p>
<div class="verdict"><strong>{_text(title)}</strong><p>{_text(summary)}</p></div></header>
{('<ol class="jump-list" aria-label="Ringkasan kandidat menurut aturan">' + items + '</ol>') if items else ''}
<section id="cakupan" aria-labelledby="cakupan-title"><h2 id="cakupan-title">Apa yang benar-benar diperiksa?</h2>
<p class="intro">Jumlah file menjelaskan cakupan, bukan nilai keamanan. Baca kendala dan pengecualian sebelum menilai hasil.</p>
<dl class="stats">{stats}</dl>
<h3>Berkas/folder yang dilewati</h3>{('<ul class="list">' + skipped + '</ul>') if skipped else '<p>Tidak ada berkas/folder yang tercatat dilewati.</p>'}
<h3>Kendala pemeriksaan</h3>{('<ul class="list">' + errors + '</ul>') if errors else '<p>Tidak ada kendala yang tercatat.</p>'}
<h3>Batas cakupan</h3><p>{_LIMITS}</p></section>
<section id="kandidat" aria-labelledby="kandidat-title"><h2 id="kandidat-title">Kandidat untuk ditinjau</h2>
<p class="intro">Prioritas adalah urutan peninjauan, bukan skor exploitability atau severity yang sudah terverifikasi. Pastikan input benar-benar dapat dikendalikan, cek validasi, lalu uji dampak pada lingkungan milik Anda.</p>
{detail if detail else '<p>Belum ada kandidat untuk ditampilkan. Ini tidak berarti aplikasi aman; lihat status dan cakupan di atas.</p>'}</section>
<section id="berikutnya" aria-labelledby="berikutnya-title"><h2 id="berikutnya-title">Setelah membaca laporan</h2>
<ol class="list"><li>Periksa lokasi kode dan jalur input. Kandidat dapat gugur bila kontrol keamanan yang relevan sudah efektif.</li><li>Jika masalah terkonfirmasi, buat perubahan sekecil mungkin dan tambahkan uji regresi.</li><li>Jalankan tes aplikasi dan pemeriksaan ini lagi. Hilangnya kandidat saja tidak membuktikan perbaikannya benar.</li></ol>
<p class="print-help">Untuk menyimpan PDF, tekan <kbd>Ctrl</kbd> + <kbd>P</kbd> (Mac: <kbd>⌘</kbd> + <kbd>P</kbd>), lalu pilih “Simpan sebagai PDF”.</p></section>
<footer>Laporan ini dapat dibaca offline; tidak memuat skrip atau aset eksternal. Rujukan hanya dibuka saat Anda mengeklik tautannya. Nama berkas dan lokasi kode dapat bersifat sensitif—tinjau sebelum membagikan laporan.</footer>
</main></div></body></html>"""


def render_markdown(report: dict) -> str:
    """Render a portable, escaped summary using only explicitly allowed schema fields."""
    coverage = report["coverage"]
    diagnostics_truncated = any(item.get("type") == "diagnostic_limit" for item in coverage.get("errors", []))
    title, summary = _summary(report)
    tool = report["tool"]
    duration = tool.get("scan_duration_ms")
    timing = [f"Waktu scanner: {duration} ms (sebelum penulisan laporan)"] if type(duration) is int and duration >= 0 else []
    parts = [
        "# Laporan KodeWaspada",
        f"Proyek: **{_markdown(report['project']['name'])}**",
        f"Dibuat: {_markdown(report['created_at'])}  \nMesin: {_markdown(tool['engine'])} {_markdown(tool['engine_version'])} · KodeWaspada {_markdown(tool['version'])}",
        *timing,
        f"Status: **{_STATUS.get(report.get('status'), 'Status pemeriksaan tidak dikenal')}**",
        f"## {title}\n\n{summary}",
        "## Cakupan",
        f"- File ditemukan: {_markdown(coverage['discovered_files'])}\n- File dipindai: {_markdown(coverage['scanned_files'])}\n- Aturan dalam cakupan: {_markdown(coverage['rule_count'])}\n- {('Entri dilewati ditampilkan' if diagnostics_truncated else 'Entri dilewati')}: {len(coverage.get('skipped', []))}",
        "### Berkas/folder yang dilewati",
        "\n".join(f"- {_markdown(item['path'])}: {_markdown(item['reason'])}" for item in coverage.get("skipped", [])) or "Tidak ada berkas/folder yang tercatat dilewati.",
        "### Kendala pemeriksaan",
        "\n".join(f"- {_markdown(item['type'])}" + (f" · {_markdown(item['path'])}" if item.get("path") else "") + f": {_markdown(item['message'])}" for item in coverage.get("errors", [])) or "Tidak ada kendala yang tercatat.",
        "### Batas cakupan\n\n" + _LIMITS,
        "## Kandidat untuk ditinjau",
        "Prioritas adalah urutan peninjauan, bukan severity terverifikasi. Setiap kandidat masih perlu ditinjau manusia.",
    ]
    if not report.get("findings"):
        parts.append("Belum ada kandidat untuk ditampilkan. Ini tidak berarti aplikasi aman; lihat status dan cakupan di atas.")
    for number, finding in enumerate(report.get("findings", []), 1):
        parts.extend([
            f"### {number:02d}. {_markdown(finding['title'])}",
            f"Prioritas: {_markdown(finding['priority'])} · **Perlu ditinjau**",
            f"Lokasi: {_markdown(_location(finding))}  \nAturan: {_markdown(finding['rule_id'])} · ID: {_markdown(finding['id'])}",
            (f"Alur statis: asal input baris {_markdown(finding['source_line'])} → operasi sensitif baris {_markdown(finding['line'])}." if finding.get("source_line") is not None else "Lokasi asal input belum tersedia; telusuri alurnya secara manual."),
        ])
        for key, label in (
            ("explanation", "Apa yang terbaca"), ("impact", "Mengapa perlu dicek"),
            ("fix", "Perbaikan yang disarankan"), ("verify", "Cara menguji ulang"),
            ("limitation", "Batas deteksi kandidat ini"), ("ai_prompt", "Prompt untuk asisten AI"),
        ):
            parts.append(f"#### {label}\n\n{_markdown(finding[key])}")
        parts.append("Jangan kirim secrets atau kode privat ke layanan AI tanpa izin. Tinjau perubahan dan hasil uji.")
        links = [f"- [Rujukan {index}](<{url}>)" for index, value in enumerate(finding.get("references", []), 1) if (url := _safe_reference(value))]
        if links:
            parts.append("#### Rujukan\n\n" + "\n".join(links))
    parts.extend([
        "## Langkah berikutnya",
        "1. Telusuri input, validasi, dan operasi sensitif pada kode.\n2. Konfirmasikan dampak pada lingkungan milik Anda sebelum menyimpulkan ada kerentanan.\n3. Perbaiki masalah yang terkonfirmasi, tambahkan uji regresi, lalu jalankan tes aplikasi dan pemeriksaan ulang.",
        "Nama berkas dan lokasi kode dapat bersifat sensitif. Tinjau sebelum membagikan laporan. Versi HTML dapat dicetak sebagai PDF dari browser.",
    ])
    return "\n\n".join(parts) + "\n"
