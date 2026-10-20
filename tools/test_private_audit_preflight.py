#!/usr/bin/env python3
"""Synthetic-only tests for offline Private preflight; NEVER fetch real user code."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("private_preflight", Path(__file__).with_name("private_audit_preflight.py"))
assert spec and spec.loader
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / "fixture"
        self.folder.mkdir()
        self.git("init", "-b", "ci/zero-history-public-build-prep-20261017")
        self.git("config", "user.name", "Synthetic")
        self.git("config", "user.email", "synthetic@example.invalid")
        self.git("remote", "add", "origin", "https://github.com/ftmstr/E-Clock.git")
        (self.folder / "Synthetic.kt").write_text("// harmless synthetic fixture\n")
        self.git("add", ".")
        self.git("commit", "-m", "synthetic source fixture")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.folder, stderr=subprocess.DEVNULL, text=True).strip()

    def fake_runner(self, calls, *, codes=(0, 0)):
        def run(args, **kwargs):
            calls.append((args, kwargs))
            return subprocess.CompletedProcess(args, codes[len(calls) - 1])
        return run

    def test_strict_all_refs_git_and_directory_sweeps_are_both_required(self):
        calls = []
        result = p.scan(self.folder, executable="/fake/gitleaks", invoke=self.fake_runner(calls))
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0][1], "git")
        self.assertIn("--log-opts=--all", calls[0][0])
        self.assertEqual(calls[1][0][1], "dir")
        self.assertEqual(result["gitleaks_all_refs"], "PASS")
        self.assertEqual(result["public_export_authorized"], False)
        self.assertEqual(result["licenses_and_rights"], "NOT VERIFIED")
        self.assertIs(calls[0][1]["stdout"], subprocess.DEVNULL)
        self.assertIs(calls[0][1]["stderr"], subprocess.DEVNULL)

    def test_secret_finding_blocks_without_leaking_output(self):
        calls = []
        with self.assertRaisesRegex(p.NoGo, "did not PASS"):
            p.scan(self.folder, executable="gitleaks", invoke=self.fake_runner(calls, codes=(1, 0)))
        self.assertEqual(len(calls), 1)

    def test_current_file_scan_failure_blocks(self):
        calls = []
        with self.assertRaisesRegex(p.NoGo, "did not PASS"):
            p.scan(self.folder, executable="gitleaks", invoke=self.fake_runner(calls, codes=(0, 2)))
        self.assertEqual(len(calls), 2)

    def test_missing_scanner_is_never_reported_as_pass(self):
        with patch.object(p.shutil, "which", return_value=None), self.assertRaisesRegex(p.NoGo, "NOT RUN"):
            p.scan(self.folder)

    def test_dirty_private_tree_blocks_scanner_execution(self):
        (self.folder / "untracked-file.txt").write_text("fixture")
        with self.assertRaisesRegex(p.NoGo, "clean"):
            p.scan(self.folder, executable="gitleaks", invoke=lambda *a, **kw: self.fail("scanner must not run"))

    def test_wrong_or_public_remote_blocks_before_scanner(self):
        self.git("remote", "set-url", "origin", "https://github.com/ftmstr/Embasic-E-Clock-Build.git")
        with self.assertRaisesRegex(p.NoGo, "not the expected Private"):
            p.scan(self.folder, executable="gitleaks", invoke=lambda *a, **kw: self.fail("scanner must not run"))

    def test_private_remote_must_match_canonical_github_origin(self):
        allowed = (
            "https://github.com/ftmstr/E-Clock.git",
            "git@github.com:ftmstr/E-Clock.git",
            "ssh://git@github.com/ftmstr/E-Clock",
        )
        for candidate in allowed:
            with self.subTest(origin=candidate):
                self.assertTrue(p.trusted_private_remote(candidate))
        forbidden = (
            "https://github.example.invalid/ftmstr/E-Clock.git",
            "https://github.com.evil.invalid/ftmstr/E-Clock.git",
            "https://github.com/another-owner/E-Clock.git",
            "https://github.com/ftmstr/Embasic-E-Clock-Build.git",
            "file:///tmp/ftmstr/E-Clock",
        )
        for candidate in forbidden:
            with self.subTest(origin=candidate):
                self.assertFalse(p.trusted_private_remote(candidate))

    def test_wrong_private_branch_blocks(self):
        self.git("checkout", "-b", "other")
        with self.assertRaisesRegex(p.NoGo, "preparation branch"):
            p.scan(self.folder, executable="gitleaks", invoke=lambda *a, **kw: self.fail("scanner must not run"))

    def test_shallow_private_checkout_is_blocked(self):
        (self.folder / "Synthetic.kt").write_text("// second synthetic commit\n")
        self.git("add", ".")
        self.git("commit", "-m", "synthetic 2")
        shallow = Path(self.tmp.name) / "shallow"
        subprocess.run(["git", "clone", "--depth", "1", "--branch", "ci/zero-history-public-build-prep-20261017", self.folder.as_uri(), str(shallow)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with self.assertRaisesRegex(p.NoGo, "shallow"):
            p.scan(shallow, executable="gitleaks", invoke=lambda *a, **kw: self.fail("scanner must not run"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
