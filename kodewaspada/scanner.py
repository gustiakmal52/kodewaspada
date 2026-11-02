"""Stage bounded source copies; never import or run the target project."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import tempfile
import unicodedata

from . import __version__

EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
UNSUPPORTED_EXTENSIONS = {".mts", ".cts"}
EXCLUDED = {"node_modules", "vendor", "dist", "build", "coverage", "outputs", "__pycache__"}
MAX_FILE_BYTES = 512_000
MAX_TOTAL_BYTES = 10_000_000
MAX_FILES = 200
MAX_ENTRIES = 20_000
MAX_ENGINE_OUTPUT = 16_000_000
MAX_DIAGNOSTIC_ITEMS = 1_000
MAX_DIAGNOSTIC_BYTES = 256_000
MAX_FINDING_ITEMS = 1_000
MAX_FINDING_BYTES = 4_000_000
RULES = Path(__file__).parent / "rules" / "javascript.json"
GUIDANCE = Path(__file__).parent / "rules" / "guidance.json"

_DIAGNOSTIC_LIMIT = {
    "type": "diagnostic_limit",
    "message": "Rincian diagnostik tambahan tidak ditampilkan karena batas laporan; cakupan belum lengkap.",
}


def display_path(value):
    """Make control and bidi characters visible in terminal and reports."""
    return "".join(f"\\u{ord(c):04x}" if unicodedata.category(c).startswith("C") else c for c in str(value))


def _json_bytes(value):
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _record_diagnostic(target, item, errors, budget):
    """Retain bounded diagnostics and one fixed truncation marker."""
    if budget["truncated"]:
        return
    item_bytes = _json_bytes(item)
    reserved_items = 1
    reserved_bytes = _json_bytes(_DIAGNOSTIC_LIMIT)
    if (budget["items"] + reserved_items >= MAX_DIAGNOSTIC_ITEMS
            or budget["bytes"] + item_bytes + reserved_bytes > MAX_DIAGNOSTIC_BYTES):
        budget["truncated"] = True
        errors.append(dict(_DIAGNOSTIC_LIMIT))
        return
    target.append(item)
    budget["items"] += 1
    budget["bytes"] += item_bytes


def _stage(root, destination):
    included, skipped, errors = [], [], []
    diagnostic_budget = {"items": 0, "bytes": 0, "truncated": False}
    discovered = total = entries = 0
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as iterator:
                for item in iterator:
                    entries += 1
                    if entries > MAX_ENTRIES:
                        _record_diagnostic(errors, {"type": "entry_limit", "message": "Batas 20.000 entri tercapai; cakupan tidak lengkap."}, errors, diagnostic_budget)
                        return included, skipped, errors, discovered
                    path = Path(item.path)
                    relative = path.relative_to(root)
                    label = display_path(relative.as_posix())
                    if item.is_symlink():
                        _record_diagnostic(skipped, {"path": label, "reason": "Tautan simbolik tidak diikuti."}, errors, diagnostic_budget)
                        continue
                    if item.is_dir(follow_symlinks=False):
                        if item.name.startswith(".") or item.name in EXCLUDED:
                            _record_diagnostic(skipped, {"path": label + "/", "reason": "Folder tersembunyi/dependensi/hasil build dikecualikan."}, errors, diagnostic_budget)
                        elif len(relative.parts) > 20:
                            _record_diagnostic(errors, {"type": "depth_limit", "message": "Kedalaman folder melebihi 20 tingkat.", "path": label}, errors, diagnostic_budget)
                        else:
                            stack.append(path)
                        continue
                    if path.suffix.lower() in UNSUPPORTED_EXTENSIONS:
                        discovered += 1
                        _record_diagnostic(skipped, {"path": label, "reason": "Ekstensi ini belum didukung konfigurasi engine."}, errors, diagnostic_budget)
                        _record_diagnostic(errors, {"type": "unsupported_extension", "message": "Ada sumber TypeScript yang belum dapat diperiksa.", "path": label}, errors, diagnostic_budget)
                        continue
                    if path.suffix.lower() not in EXTENSIONS:
                        continue
                    discovered += 1
                    if item.name.startswith(".") or not item.is_file(follow_symlinks=False):
                        _record_diagnostic(skipped, {"path": label, "reason": "Berkas tersembunyi/non-reguler tidak dibaca."}, errors, diagnostic_budget)
                        continue
                    if len(included) >= MAX_FILES:
                        _record_diagnostic(errors, {"type": "file_limit", "message": "Batas 200 berkas tercapai; bagi proyek menjadi folder yang lebih kecil."}, errors, diagnostic_budget)
                        return included, skipped, errors, discovered
                    # Open without following a file symlink changed since enumeration.
                    try:
                        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                        with os.fdopen(descriptor, "rb") as handle:
                            info = os.fstat(handle.fileno())
                            if not stat.S_ISREG(info.st_mode):
                                raise ValueError("nonregular")
                            data = handle.read(MAX_FILE_BYTES + 1)
                        if len(data) > MAX_FILE_BYTES:
                            raise ValueError("large")
                        data.decode("utf-8")
                        if b"\0" in data:
                            raise ValueError("binary")
                    except (OSError, ValueError, UnicodeError):
                        _record_diagnostic(skipped, {"path": label, "reason": "Tidak terbaca, bukan UTF-8, non-reguler, atau lebih dari 512 KB."}, errors, diagnostic_budget)
                        _record_diagnostic(errors, {"type": "unreadable_source", "message": "Sebagian sumber tidak dapat dianalisis.", "path": label}, errors, diagnostic_budget)
                        continue
                    total += len(data)
                    if total > MAX_TOTAL_BYTES:
                        _record_diagnostic(errors, {"type": "size_limit", "message": "Batas total 10 MB tercapai; cakupan tidak lengkap."}, errors, diagnostic_budget)
                        return included, skipped, errors, discovered
                    copy = destination / relative
                    copy.parent.mkdir(parents=True, exist_ok=True)
                    copy.write_bytes(data)
                    included.append(relative.as_posix())
        except OSError:
            _record_diagnostic(errors, {"type": "unreadable_directory", "message": "Folder tidak dapat dibaca.", "path": display_path(directory.relative_to(root))}, errors, diagnostic_budget)
    return included, skipped, errors, discovered


def engine_command(engine, stage):
    return [engine, "scan", "--oss-only", "--config", str(RULES), "--json", "--quiet",
            "--metrics=off", "--disable-version-check", "--disable-nosem", "--no-git-ignore",
            "--no-rewrite-rule-ids", "--jobs=1", "--timeout=5", "--max-memory=512",
            f"--max-target-bytes={MAX_FILE_BYTES}", str(stage)]


def _run_engine(engine, stage, temporary):
    # Do not inherit app tokens, Python injection options, or target configuration.
    environment = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL", "SYSTEMROOT") if key in os.environ}
    environment.update({"SEMGREP_SEND_METRICS": "off", "SEMGREP_ENABLE_VERSION_CHECK": "0",
                        "SEMGREP_SETTINGS_FILE": str(temporary / "settings.yml"),
                        "SEMGREP_LOG_FILE": str(temporary / "engine.log")})
    import resource

    def output_limit():
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_ENGINE_OUTPUT, MAX_ENGINE_OUTPUT))

    with (temporary / "stdout.json").open("wb") as stdout, (temporary / "stderr.txt").open("wb") as stderr:
        process = subprocess.Popen(engine_command(engine, stage), cwd=temporary, env=environment,
                                   stdout=stdout, stderr=stderr, start_new_session=True, preexec_fn=output_limit)
        try:
            process.wait(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise RuntimeError("engine_timeout") from None
    output = temporary / "stdout.json"
    if output.stat().st_size >= MAX_ENGINE_OUTPUT:
        raise RuntimeError("output_limit")
    if process.returncode not in (0, 1):
        raise RuntimeError("engine_failure")
    try:
        payload = json.loads(output.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError):
        raise RuntimeError("invalid_engine_output") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise RuntimeError("invalid_engine_output")
    return payload


def _relative_engine_path(value, stage, included):
    path = Path(str(value))
    if path.is_absolute():
        try:
            path = path.relative_to(stage)
        except ValueError:
            return None
    value = path.as_posix()
    if value in included:
        return value
    # Some versions report targets relative to the temporary working directory.
    if value.startswith("source/") and value[7:] in included:
        return value[7:]
    return None


def normalize(payload, stage, included, guidance):
    findings, errors = [], []
    finding_bytes = 0
    seen = set()
    for result in payload["results"]:
        if not isinstance(result, dict):
            raise ValueError("invalid result")
        rule = result.get("check_id")
        path = _relative_engine_path(result.get("path", ""), stage, included)
        if rule not in guidance or path is None:
            raise ValueError("unexpected rule or path")
        line = result.get("start", {}).get("line")
        end = result.get("end", {}).get("line")
        if not isinstance(line, int) or not isinstance(end, int) or line < 1 or end < line:
            raise ValueError("invalid location")
        identity = (rule, path, line)
        if identity in seen:
            continue
        item = dict(guidance[rule])
        item.update({"id": f"KW-{len(findings)+1:03d}", "rule_id": rule, "status": "needs_review",
                     "path": display_path(path), "line": line, "end_line": end, "source_line": None})
        item_bytes = _json_bytes(item)
        if len(findings) >= MAX_FINDING_ITEMS or finding_bytes + item_bytes > MAX_FINDING_BYTES:
            errors.append({"type": "finding_limit", "message": "Batas kandidat laporan tercapai; analisis belum lengkap."})
            break
        seen.add(identity)
        findings.append(item)
        finding_bytes += item_bytes
    if payload.get("errors"):
        # Raw engine messages may contain source text, secrets or local paths.
        errors.append({"type": "engine_diagnostic", "message": "Engine melaporkan masalah parsing/analisis. Cakupan tidak lengkap."})
    if payload.get("skipped_rules"):
        errors.append({"type": "skipped_rules", "message": "Engine melewati sebagian aturan; analisis belum lengkap."})
    scanned = set()
    for value in payload.get("paths", {}).get("scanned", []):
        path = _relative_engine_path(value, stage, included)
        if path is not None:
            scanned.add(path)
    if len(scanned) != len(included):
        errors.append({"type": "coverage_gap", "message": "Engine tidak mengonfirmasi analisis semua berkas yang disiapkan."})
    return findings, errors, len(scanned)


def scan(root):
    root = Path(root).expanduser()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Pilih folder proyek lokal, bukan URL, berkas, atau tautan simbolik.")
    root = root.resolve()
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("Versi awal mendukung Linux/macOS; gunakan WSL di Windows.")
    engine = shutil.which("semgrep")
    if engine is None:
        raise ValueError("Semgrep belum tersedia. Instal requirements-engine.txt pada lingkungan terpisah.")
    if Path(engine).resolve().is_relative_to(root):
        raise ValueError("Engine di dalam proyek target tidak dijalankan. Gunakan instalasi Semgrep terpisah.")
    guidance = json.loads(GUIDANCE.read_text(encoding="utf-8"))
    report = {"schema_version": 1, "tool": {"name": "KodeWaspada", "version": __version__,
              "engine": "Semgrep CE", "engine_version": "unknown"},
              "project": {"name": display_path(root.name)}, "created_at": datetime.now(timezone.utc).isoformat(),
              "status": "failed", "coverage": {"discovered_files": 0, "scanned_files": 0,
              "rule_count": len(guidance), "skipped": [], "errors": []}, "findings": []}
    with tempfile.TemporaryDirectory(prefix="kodewaspada-") as folder:
        temporary = Path(folder)
        stage = temporary / "source"
        stage.mkdir()
        # Replace target ignore policies; exclusions must be visible in our report.
        (stage / ".semgrepignore").write_text("", encoding="utf-8")
        included, skipped, errors, discovered = _stage(root, stage)
        report["coverage"].update(discovered_files=discovered, skipped=skipped, errors=errors)
        if not included:
            errors.append({"type": "no_sources", "message": "Tidak ada sumber JavaScript/TypeScript yang dapat diperiksa."})
            return report
        try:
            payload = _run_engine(engine, stage, temporary)
            findings, diagnostics, scanned = normalize(payload, stage, set(included), guidance)
            report["findings"] = findings
            report["coverage"]["scanned_files"] = scanned
            errors.extend(diagnostics)
            version = payload.get("version", "unknown")
            report["tool"]["engine_version"] = display_path(str(version))[:40]
            report["status"] = "partial" if errors else "completed"
        except (OSError, RuntimeError, ValueError, TypeError, AttributeError):
            errors.append({"type": "engine_failure", "message": "Analisis tidak selesai. Periksa instalasi engine dan coba folder yang lebih kecil; tidak ada kesimpulan aman."})
    return report
