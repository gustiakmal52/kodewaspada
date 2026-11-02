#!/usr/bin/env python3
"""Build a reproducible, self-contained KodeWaspada skill archive."""

from __future__ import annotations

import argparse
import grp
import hashlib
import os
from pathlib import Path
import pwd
import re
import stat
import sys
import tomllib
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = "kodewaspada"
EXPECTED_SKILL_FILES = frozenset(
    {
        "LICENSE",
        "SKILL.md",
        "agents/openai.yaml",
        "references/fix-and-retest.md",
        "references/review-patterns.md",
    }
)
MAX_FILES = 500
MAX_FILE_SIZE = 25 * 1024 * 1024
MAX_ARCHIVE_SIZE = 50 * 1024 * 1024
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\Z")
RELEASE_LICENSE_SHA256 = "ba07543136d2bf82a88598f86c4373bd3a94a0639419c971c623a499dd69d7b8"


class BundleError(ValueError):
    """The requested bundle cannot be produced safely."""


def read_version(pyproject: Path) -> str:
    """Read the project version without importing or executing project code."""
    try:
        with pyproject.open("rb") as handle:
            version = tomllib.load(handle)["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        raise BundleError(f"Tidak dapat membaca versi dari {pyproject}: {exc}") from exc
    if not isinstance(version, str) or not _VERSION.fullmatch(version):
        raise BundleError("Versi project harus berupa teks aman untuk nama berkas.")
    return version


def sidecar_path(output: Path) -> Path:
    return output.with_name(f"{output.name}.sha256")


def _exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _validate_component(name: str) -> None:
    if name in {"", ".", ".."} or "/" in name or "\\" in name:
        raise BundleError(f"Nama path tidak aman untuk arsip: {name!r}")


def _collect_files(source: Path) -> list[tuple[str, Path]]:
    try:
        root_mode = source.lstat().st_mode
    except OSError as exc:
        raise BundleError(f"Folder skill tidak dapat dibaca: {source}") from exc
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        raise BundleError("Sumber skill harus berupa direktori biasa, bukan symlink.")

    files: list[tuple[str, Path]] = []
    seen: set[str] = set()
    stack = [(source, ())]
    while stack:
        directory, parent_parts = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise BundleError(f"Direktori tidak dapat dibaca: {directory}") from exc
        for entry in entries:
            _validate_component(entry.name)
            relative_parts = (*parent_parts, entry.name)
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise BundleError(f"Entry tidak dapat diperiksa: {entry.path}") from exc
            mode = metadata.st_mode
            if stat.S_ISLNK(mode):
                raise BundleError(f"Symlink tidak boleh masuk bundle: {entry.path}")
            if stat.S_ISDIR(mode):
                stack.append((Path(entry.path), relative_parts))
                continue
            if not stat.S_ISREG(mode):
                raise BundleError(f"Hanya berkas biasa yang boleh masuk bundle: {entry.path}")
            if metadata.st_size > MAX_FILE_SIZE:
                raise BundleError(f"Berkas melebihi batas {MAX_FILE_SIZE} byte: {entry.path}")

            relative_name = "/".join(relative_parts)
            if relative_name not in EXPECTED_SKILL_FILES:
                raise BundleError(f"Berkas di luar allowlist skill: {relative_name}")
            archive_name = "/".join((ARCHIVE_ROOT, relative_name))
            folded_name = archive_name.casefold()
            if folded_name in seen:
                raise BundleError(f"Nama arsip bertabrakan tanpa membedakan kapital: {archive_name}")
            seen.add(folded_name)
            files.append((archive_name, Path(entry.path)))
            if len(files) > MAX_FILES:
                raise BundleError(f"Jumlah berkas melebihi batas {MAX_FILES}.")

    actual_files = {name.removeprefix(f"{ARCHIVE_ROOT}/") for name, _ in files}
    missing_files = EXPECTED_SKILL_FILES - actual_files
    if missing_files:
        raise BundleError(f"Berkas wajib skill tidak ada: {', '.join(sorted(missing_files))}")
    skill_files = [name for name, _ in files if Path(name).name.casefold() == "skill.md"]
    expected_skill = f"{ARCHIVE_ROOT}/SKILL.md"
    if len(skill_files) != 1 or skill_files[0].casefold() != expected_skill.casefold():
        raise BundleError("Bundle harus memiliki tepat satu SKILL.md pada root skill.")
    return sorted(files)


def _read_regular_file(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise BundleError(f"Berkas tidak dapat dibuka dengan aman: {path}") from exc
    with os.fdopen(descriptor, "rb") as handle:
        metadata = os.fstat(handle.fileno())
        if not stat.S_ISREG(metadata.st_mode):
            raise BundleError(f"Entry berubah menjadi nonregular: {path}")
        if metadata.st_size > MAX_FILE_SIZE:
            raise BundleError(f"Berkas melebihi batas {MAX_FILE_SIZE} byte: {path}")
        data = handle.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise BundleError(f"Berkas melebihi batas {MAX_FILE_SIZE} byte: {path}")
    return data


def _zip_info(name: str, *, directory: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
    info.create_system = 3
    if directory:
        info.compress_type = zipfile.ZIP_STORED
        info.external_attr = ((stat.S_IFDIR | 0o755) << 16) | 0x10
    else:
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (stat.S_IFREG | 0o644) << 16
    return info


def _write_archive(handle, files: list[tuple[str, Path]]) -> None:
    with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(_zip_info(f"{ARCHIVE_ROOT}/", directory=True), b"")
        for archive_name, source_path in files:
            data = _read_regular_file(source_path)
            if (archive_name == f"{ARCHIVE_ROOT}/LICENSE"
                    and hashlib.sha256(data).hexdigest() != RELEASE_LICENSE_SHA256):
                raise BundleError("LICENSE yang akan diarsipkan tidak cocok dengan teks rilis kanonis.")
            archive.writestr(_zip_info(archive_name), data)
            if archive.fp is not None and archive.fp.tell() > MAX_ARCHIVE_SIZE:
                raise BundleError(f"ZIP melebihi batas {MAX_ARCHIVE_SIZE} byte.")
    handle.flush()
    if os.fstat(handle.fileno()).st_size > MAX_ARCHIVE_SIZE:
        raise BundleError(f"ZIP melebihi batas {MAX_ARCHIVE_SIZE} byte.")


def _sha256(handle) -> str:
    digest = hashlib.sha256()
    handle.seek(0)
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def _identity(metadata: os.stat_result) -> tuple[int, int]:
    return metadata.st_dev, metadata.st_ino


def _path_identity(path: Path) -> tuple[int, int]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise BundleError(f"Artefak berubah atau hilang saat dibuat: {path}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise BundleError(f"Artefak berubah menjadi nonregular: {path}")
    return _identity(metadata)


def _name_identity(parent_fd: int, name: str) -> tuple[int, int]:
    try:
        metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as exc:
        raise BundleError(f"Artefak berubah atau hilang saat dibuat: {name}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise BundleError(f"Artefak berubah menjadi nonregular: {name}")
    return _identity(metadata)


def _unlink_at_if_identity(parent_fd: int, name: str, expected: tuple[int, int] | None) -> None:
    if expected is None:
        return
    try:
        if _name_identity(parent_fd, name) == expected:
            os.unlink(name, dir_fd=parent_fd)
    except (BundleError, OSError):
        pass


def _group_is_private(metadata: os.stat_result) -> bool:
    owner = pwd.getpwuid(metadata.st_uid).pw_name
    members = set(grp.getgrgid(metadata.st_gid).gr_mem)
    members.update(account.pw_name for account in pwd.getpwall() if account.pw_gid == metadata.st_gid)
    return members <= {owner}


def _shared_write_is_safe(metadata: os.stat_result, child_owner: int | None) -> bool:
    shared_writable = bool(metadata.st_mode & stat.S_IWOTH)
    if metadata.st_mode & stat.S_IWGRP:
        try:
            shared_writable = shared_writable or not _group_is_private(metadata)
        except (KeyError, OSError):
            shared_writable = True
    if not shared_writable:
        return True
    return bool(metadata.st_mode & stat.S_ISVTX
                and child_owner == os.geteuid()
                and metadata.st_uid in {0, os.geteuid()})


def _validate_output_parent(parent: Path) -> tuple[int, int]:
    if not sys.platform.startswith("linux"):
        raise BundleError("Builder rilis yang memeriksa ACL saat ini hanya didukung di Linux/WSL.")
    absolute = parent.absolute()
    try:
        resolved = absolute.resolve(strict=True)
    except OSError as exc:
        raise BundleError(f"Folder output tidak dapat diperiksa: {parent}") from exc
    if resolved != absolute:
        raise BundleError("Folder output harus direktori biasa, bukan symlink.")
    child_owner = None
    current = absolute
    while True:
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise BundleError(f"Komponen folder output tidak dapat diperiksa: {current}") from exc
        if not stat.S_ISDIR(metadata.st_mode):
            raise BundleError("Semua komponen folder output harus direktori biasa.")
        try:
            if any("acl" in name.casefold() for name in os.listxattr(current, follow_symlinks=False)):
                raise BundleError(f"ACL tambahan pada jalur output tidak didukung: {current}")
        except OSError as exc:
            raise BundleError(f"ACL jalur output tidak dapat diperiksa: {current}") from exc
        if not _shared_write_is_safe(metadata, child_owner):
            raise BundleError("Jalur output tidak boleh dapat diganti oleh akun lain.")
        if current == absolute and metadata.st_uid != os.geteuid():
            raise BundleError("Folder output harus dimiliki pengguna saat ini.")
        if current.parent == current:
            return _identity(absolute.lstat())
        child_owner, current = metadata.st_uid, current.parent


def _validate_release_license() -> None:
    root_license = (REPO_ROOT / "LICENSE").read_bytes()
    skill_license = (REPO_ROOT / "skills" / ARCHIVE_ROOT / "LICENSE").read_bytes()
    digest = hashlib.sha256(root_license).hexdigest()
    if root_license != skill_license or digest != RELEASE_LICENSE_SHA256:
        raise BundleError("Lisensi root dan bundle harus identik dengan teks rilis PolyForm Noncommercial yang ditinjau.")


def build_bundle(source: Path, output: Path) -> tuple[Path, Path, str]:
    """Build and publish a bundle plus a sha256sum-compatible sidecar."""
    source, output = Path(source), Path(output)
    checksum = sidecar_path(output)
    if _exists(output) or _exists(checksum):
        raise FileExistsError("Output atau sidecar sudah ada; artefak lama tidak ditimpa.")

    files = _collect_files(source)
    _validate_component(output.name)
    _validate_component(checksum.name)
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    parent_fd = os.open(output.parent, parent_flags)
    parent_identity = _identity(os.fstat(parent_fd))
    output_identity = sidecar_identity = None
    try:
        if _validate_output_parent(output.parent) != parent_identity:
            raise BundleError("Folder output berubah sebelum pembuatan bundle.")
        file_flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
        descriptor = os.open(output.name, file_flags, 0o600, dir_fd=parent_fd)
        with os.fdopen(descriptor, "w+b") as output_handle:
            output_identity = _identity(os.fstat(output_handle.fileno()))
            _write_archive(output_handle, files)
            digest = _sha256(output_handle)
        if _name_identity(parent_fd, output.name) != output_identity:
            raise BundleError("Bundle berubah setelah diverifikasi.")
        sidecar_descriptor = os.open(checksum.name, file_flags, 0o600, dir_fd=parent_fd)
        with os.fdopen(sidecar_descriptor, "w", encoding="ascii", newline="\n") as sidecar_handle:
            sidecar_identity = _identity(os.fstat(sidecar_handle.fileno()))
            sidecar_handle.write(f"{digest}  {output.name}\n")
            sidecar_handle.flush()
        if (_name_identity(parent_fd, checksum.name) != sidecar_identity
                or _name_identity(parent_fd, output.name) != output_identity
                or _validate_output_parent(output.parent) != parent_identity):
            raise BundleError("Jalur output berubah saat bundle dibuat.")
    except Exception:
        _unlink_at_if_identity(parent_fd, checksum.name, sidecar_identity)
        _unlink_at_if_identity(parent_fd, output.name, output_identity)
        raise
    finally:
        os.close(parent_fd)
    return output, checksum, digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Path ZIP tujuan; default memakai outputs/ dan versi project.")
    args = parser.parse_args(argv)
    try:
        _validate_release_license()
        version = read_version(REPO_ROOT / "pyproject.toml")
        output = args.output or REPO_ROOT / "outputs" / f"kodewaspada-skill-{version}.zip"
        output, checksum, digest = build_bundle(REPO_ROOT / "skills" / ARCHIVE_ROOT, output.expanduser().absolute())
    except (BundleError, FileExistsError, OSError) as exc:
        parser.error(str(exc))
    print(f"Bundle: {output}")
    print(f"SHA-256: {digest}")
    print(f"Sidecar: {checksum}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
