import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .scanner import scan
from .report import render_html, render_markdown


def main(argv=None):
    parser = argparse.ArgumentParser(description="KodeWaspada: pahami risiko kode sebelum deploy. Analisis lokal, bukan sertifikat aman.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    scan_parser = commands.add_parser("scan", help="Periksa folder kode JS/TS tanpa menjalankan proyek")
    scan_parser.add_argument("path", type=Path)
    scan_parser.add_argument("--out", type=Path, required=True, help="Folder laporan baru; tidak boleh sudah ada")
    args = parser.parse_args(argv)
    output = args.out.expanduser().absolute()
    if output.exists() or output.is_symlink():
        parser.error("Folder output sudah ada. Pilih nama baru agar laporan lama tidak tertimpa.")
    try:
        report = scan(args.path)
        output.mkdir(mode=0o700, parents=True, exist_ok=False)
        with (output / "report.json").open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        with (output / "report.html").open("x", encoding="utf-8") as handle:
            handle.write(render_html(report))
        with (output / "report.md").open("x", encoding="utf-8") as handle:
            handle.write(render_markdown(report))
    except (OSError, ValueError) as error:
        # Do not print unexpected raw filesystem or engine content.
        if isinstance(error, ValueError):
            print(str(error), file=sys.stderr)
        else:
            print("Tidak dapat membaca proyek atau menulis laporan. Periksa izin dan gunakan folder output baru.", file=sys.stderr)
        return 2
    count = len(report["findings"])
    print(f"KodeWaspada: {count} kandidat perlu ditinjau; status analisis: {report['status']}.")
    print(f"Cakupan: {report['coverage']['scanned_files']} berkas; {report['coverage']['rule_count']} aturan.")
    duration = report["tool"].get("scan_duration_ms")
    if type(duration) is int and duration >= 0:
        print(f"Waktu scanner: {duration} ms (sebelum penulisan laporan).")
    print("Buka report.html di folder output. Jangan publikasikan laporan proyek privat tanpa meninjaunya.")
    print("Nol kandidat bukan bukti aman. Kontrol akses, RLS, dependensi, dan rahasia belum diperiksa.")
    return 2 if report["status"] != "completed" else (1 if count else 0)
