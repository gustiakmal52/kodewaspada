from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import kodewaspada
from scripts import build_skill_bundle as bundle


ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def make_skill(self) -> Path:
        source = self.root / "fixture" / "kodewaspada"
        (source / "agents").mkdir(parents=True)
        (source / "references").mkdir(parents=True)
        (source / "SKILL.md").write_text("---\nname: kodewaspada\n---\n", encoding="utf-8")
        (source / "LICENSE").write_bytes((ROOT / "LICENSE").read_bytes())
        (source / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
        (source / "references" / "fix-and-retest.md").write_text("synthetic fix reference\n", encoding="utf-8")
        (source / "references" / "review-patterns.md").write_text("synthetic review reference\n", encoding="utf-8")
        return source

    def test_project_and_runtime_versions_match(self):
        self.assertEqual(bundle.read_version(ROOT / "pyproject.toml"), kodewaspada.__version__)

    def test_real_skill_has_one_root_and_required_files(self):
        output = self.root / "real.zip"
        bundle.build_bundle(ROOT / "skills" / "kodewaspada", output)
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
            self.assertEqual(names, sorted(names))
            self.assertEqual({PurePosixPath(name).parts[0] for name in names}, {"kodewaspada"})
            self.assertEqual(sum(PurePosixPath(name).name.casefold() == "skill.md" for name in names), 1)
            self.assertIn("kodewaspada/SKILL.md", names)
            self.assertIn("kodewaspada/LICENSE", names)
            self.assertIn("kodewaspada/agents/openai.yaml", names)
            self.assertIn("kodewaspada/references/fix-and-retest.md", names)
            bundled_license = archive.read("kodewaspada/LICENSE")
            self.assertEqual(bundled_license, (ROOT / "LICENSE").read_bytes())
            self.assertIn(b"Required Notice: Copyright 2026 EL1Syum", bundled_license)
            for info in archive.infolist():
                self.assertEqual(info.date_time, bundle.ZIP_TIMESTAMP)
                self.assertFalse(stat.S_ISLNK(info.external_attr >> 16))

    def test_archive_is_reproducible_at_two_output_paths(self):
        source = self.make_skill()
        first = self.root / "first.zip"
        second = self.root / "elsewhere" / "second.zip"
        bundle.build_bundle(source, first)
        bundle.build_bundle(source, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_sidecar_contains_exact_archive_hash(self):
        output = self.root / "bundle.zip"
        _, sidecar, returned_digest = bundle.build_bundle(self.make_skill(), output)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        self.assertEqual(returned_digest, digest)
        self.assertEqual(sidecar, self.root / "bundle.zip.sha256")
        self.assertEqual(sidecar.read_text(encoding="ascii"), f"{digest}  bundle.zip\n")

    def test_default_name_uses_version_from_pyproject(self):
        repo = self.root / "repo"
        source = repo / "skills" / "kodewaspada"
        source.parent.mkdir(parents=True)
        fixture = self.make_skill()
        for path in fixture.rglob("*"):
            target = source / path.relative_to(fixture)
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
        (repo / "pyproject.toml").write_text('[project]\nversion = "9.8.7"\n', encoding="utf-8")
        release_license = (ROOT / "LICENSE").read_bytes()
        (repo / "LICENSE").write_bytes(release_license)
        (source / "LICENSE").write_bytes(release_license)
        with patch.object(bundle, "REPO_ROOT", repo), redirect_stdout(io.StringIO()):
            self.assertEqual(bundle.main([]), 0)
            explicit = self.root / "custom-name.zip"
            self.assertEqual(bundle.main(["--output", str(explicit)]), 0)
        self.assertTrue((repo / "outputs" / "kodewaspada-skill-9.8.7.zip").is_file())
        self.assertTrue(explicit.is_file())

    def test_traversal_style_name_and_symlink_are_rejected(self):
        source = self.make_skill()
        (source / "..\\escape.txt").write_text("outside on Windows", encoding="utf-8")
        with self.assertRaises(bundle.BundleError):
            bundle.build_bundle(source, self.root / "traversal.zip")
        (source / "..\\escape.txt").unlink()
        (source / "linked-license").symlink_to(source / "LICENSE")
        with self.assertRaises(bundle.BundleError):
            bundle.build_bundle(source, self.root / "symlink.zip")
        self.assertFalse((self.root / "traversal.zip").exists())
        self.assertFalse((self.root / "symlink.zip").exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO tidak didukung platform ini")
    def test_nonregular_file_is_rejected_without_opening_it(self):
        source = self.make_skill()
        os.mkfifo(source / "pipe")
        with self.assertRaises(bundle.BundleError):
            bundle.build_bundle(source, self.root / "fifo.zip")

    def test_skill_manifest_must_be_unique_and_at_root(self):
        source = self.make_skill()
        (source / "skill.MD").write_text("duplicate", encoding="utf-8")
        with self.assertRaises(bundle.BundleError):
            bundle.build_bundle(source, self.root / "duplicate.zip")
        (source / "skill.MD").unlink()
        (source / "SKILL.md").rename(source / "references" / "SKILL.md")
        with self.assertRaises(bundle.BundleError):
            bundle.build_bundle(source, self.root / "nested.zip")

    def test_existing_output_or_sidecar_is_never_overwritten(self):
        source = self.make_skill()
        output = self.root / "existing.zip"
        output.write_bytes(b"KEEP_OUTPUT")
        with self.assertRaises(FileExistsError):
            bundle.build_bundle(source, output)
        self.assertEqual(output.read_bytes(), b"KEEP_OUTPUT")

        fresh = self.root / "fresh.zip"
        sidecar = bundle.sidecar_path(fresh)
        sidecar.write_text("KEEP_SIDECAR", encoding="ascii")
        with self.assertRaises(FileExistsError):
            bundle.build_bundle(source, fresh)
        self.assertFalse(fresh.exists())
        self.assertEqual(sidecar.read_text(encoding="ascii"), "KEEP_SIDECAR")

    def test_unexpected_local_file_fails_closed(self):
        source = self.make_skill()
        (source / "private-notes.txt").write_text("must not ship\n", encoding="utf-8")
        output = self.root / "unexpected.zip"
        with self.assertRaisesRegex(bundle.BundleError, "allowlist"):
            bundle.build_bundle(source, output)
        self.assertFalse(output.exists())
        self.assertFalse(bundle.sidecar_path(output).exists())

    def test_limits_are_enforced_without_large_fixtures(self):
        source = self.make_skill()
        cases = [
            ("MAX_FILES", 2, "files.zip"),
            ("MAX_FILE_SIZE", 4, "file-size.zip"),
            ("MAX_ARCHIVE_SIZE", 1, "archive-size.zip"),
        ]
        for constant, limit, filename in cases:
            output = self.root / filename
            with self.subTest(constant=constant), patch.object(bundle, constant, limit):
                with self.assertRaises(bundle.BundleError):
                    bundle.build_bundle(source, output)
                self.assertFalse(output.exists())
                self.assertFalse(bundle.sidecar_path(output).exists())

    def test_write_size_hash_and_published_output_use_one_inode(self):
        source = self.make_skill()
        output = self.root / "same-inode.zip"
        identities = []
        write_archive = bundle._write_archive
        sha256 = bundle._sha256

        def record_write(handle, files):
            identities.append(bundle._identity(os.fstat(handle.fileno())))
            return write_archive(handle, files)

        def record_hash(handle):
            identities.append(bundle._identity(os.fstat(handle.fileno())))
            return sha256(handle)

        with patch.object(bundle, "_write_archive", side_effect=record_write), patch.object(bundle, "_sha256", side_effect=record_hash):
            bundle.build_bundle(source, output)
        identities.append(bundle._path_identity(output))
        self.assertEqual(len(set(identities)), 1)

    def test_output_parent_substitution_fails_and_cleans_pinned_directory(self):
        source = self.make_skill()
        parent = self.root / "checked"
        parent.mkdir()
        output = parent / "substitution.zip"
        moved = self.root / "checked-original"
        validate = bundle._validate_output_parent
        swapped = False

        def substitute(path):
            nonlocal swapped
            identity = validate(path)
            if not swapped:
                swapped = True
                path.rename(moved)
                path.mkdir(mode=0o777)
                path.chmod(0o777)
            return identity

        with patch.object(bundle, "_validate_output_parent", side_effect=substitute):
            with self.assertRaises(bundle.BundleError):
                bundle.build_bundle(source, output)
        self.assertFalse(output.exists())
        self.assertFalse(bundle.sidecar_path(output).exists())
        self.assertFalse((moved / output.name).exists())
        self.assertFalse((moved / bundle.sidecar_path(output).name).exists())

    @unittest.skipUnless(hasattr(os, "geteuid"), "Izin POSIX tidak didukung platform ini")
    def test_shared_writable_output_parent_is_rejected(self):
        source = self.make_skill()
        shared = self.root / "shared"
        shared.mkdir(mode=0o777)
        shared.chmod(0o777)
        output = shared / "bundle.zip"
        with self.assertRaisesRegex(bundle.BundleError, "akun lain"):
            bundle.build_bundle(source, output)
        self.assertFalse(output.exists())

    @unittest.skipUnless(shutil.which("setfacl"), "setfacl tidak tersedia")
    def test_named_user_acl_on_ancestor_is_rejected(self):
        source = self.make_skill()
        ancestor = self.root / "acl-ancestor"
        parent = ancestor / "output"
        parent.mkdir(parents=True)
        subprocess.run(["setfacl", "-m", "u:nobody:rwx", str(ancestor)], check=True)
        with self.assertRaisesRegex(bundle.BundleError, "ACL tambahan"):
            bundle.build_bundle(source, parent / "bundle.zip")

    def test_attacker_owned_sticky_ancestor_is_not_trusted(self):
        metadata = type("Metadata", (), {"st_mode": stat.S_IFDIR | 0o1777, "st_uid": os.geteuid() + 1})()
        with patch.object(bundle, "_group_is_private", return_value=True):
            self.assertFalse(bundle._shared_write_is_safe(metadata, os.geteuid()))

    def test_release_builder_rejects_license_mismatch(self):
        repo = self.root / "repo"
        source = repo / "skills" / "kodewaspada"
        source.parent.mkdir(parents=True)
        fixture = self.make_skill()
        for path in fixture.rglob("*"):
            target = source / path.relative_to(fixture)
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
        (repo / "pyproject.toml").write_text('[project]\nversion = "1.0.0"\n', encoding="utf-8")
        (repo / "LICENSE").write_text("different\n", encoding="utf-8")
        with patch.object(bundle, "REPO_ROOT", repo), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                bundle.main([])
        self.assertEqual(caught.exception.code, 2)

    def test_release_builder_rejects_matching_but_incomplete_license(self):
        repo = self.root / "repo"
        source = repo / "skills" / "kodewaspada"
        source.parent.mkdir(parents=True)
        fixture = self.make_skill()
        for path in fixture.rglob("*"):
            target = source / path.relative_to(fixture)
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
        (repo / "pyproject.toml").write_text('[project]\nversion = "1.0.0"\n', encoding="utf-8")
        incomplete = (
            b"Required Notice: Copyright 2026 EL1Syum\n\n"
            b"# PolyForm Noncommercial License 1.0.0\n\n"
            b"https://polyformproject.org/licenses/noncommercial/1.0.0\n"
        )
        (repo / "LICENSE").write_bytes(incomplete)
        (source / "LICENSE").write_bytes(incomplete)
        with patch.object(bundle, "REPO_ROOT", repo), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                bundle.main([])
        self.assertEqual(caught.exception.code, 2)

    def test_license_mutation_after_precheck_is_rejected(self):
        repo = self.root / "repo"
        source = repo / "skills" / "kodewaspada"
        source.parent.mkdir(parents=True)
        fixture = self.make_skill()
        for path in fixture.rglob("*"):
            target = source / path.relative_to(fixture)
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
        (repo / "pyproject.toml").write_text('[project]\nversion = "0.2.0"\n', encoding="utf-8")
        (repo / "LICENSE").write_bytes((ROOT / "LICENSE").read_bytes())
        output = self.root / "mutated-license.zip"

        def mutate_license(_):
            (source / "LICENSE").write_text("MODIFIED AFTER VALIDATION\n", encoding="utf-8")
            return "0.2.0"

        with (patch.object(bundle, "REPO_ROOT", repo),
              patch.object(bundle, "read_version", side_effect=mutate_license),
              redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO())):
            with self.assertRaises(SystemExit) as caught:
                bundle.main(["--output", str(output)])
        self.assertEqual(caught.exception.code, 2)
        self.assertFalse(output.exists())
        self.assertFalse(bundle.sidecar_path(output).exists())


if __name__ == "__main__":
    unittest.main()
