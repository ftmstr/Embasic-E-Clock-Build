#!/usr/bin/env python3
"""Synthetic Gradle dependency-list regression tests. No Private files read."""
import importlib.util
from pathlib import Path
import subprocess
import stat
import sys
import tempfile
from unittest.mock import patch
import unittest

spec = importlib.util.spec_from_file_location("dep_preflight", Path(__file__).with_name("gradle_dependency_preflight.py"))
assert spec and spec.loader
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-b", "ci/zero-history-public-build-prep-20261017")
        self.git("config", "user.name", "Synthetic Tester")
        self.git("config", "user.email", "synthetic@example.invalid")
        self.git("remote", "add", "origin", "https://github.com/ftmstr/E-Clock.git")
        (self.root / "Synthetic.kt").write_text("// synthetic fixture only\n")
        self.git("add", ".")
        self.git("commit", "-m", "synthetic commit")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True, stderr=subprocess.DEVNULL).strip()

    @staticmethod
    def synthetic_graph():
        return """debugRuntimeClasspath - synthetic test fixture
+--- androidx.compose.runtime:runtime:1.9.4
|    +--- org.jetbrains.kotlin:kotlin-stdlib:2.2.0 -> 2.2.10
|    \\--- com.google.android.gms:play-services-wearable:20.0.1 (*)
\\--- androidx.core:core:1.19.0
"""

    def runner(self, calls, code=0, payload=None):
        text = self.synthetic_graph() if payload is None else payload
        def run(args, **kw):
            calls.append(args)
            return subprocess.CompletedProcess(args, code, stdout=text)
        return run

    def test_extracts_transitive_and_selected_version_without_license_claims(self):
        calls = []
        report = d.collect(self.root, "fake-gradle", self.runner(calls))
        self.assertEqual(len(calls), 12)
        self.assertEqual(report["requested_configurations"], 12)
        self.assertIn("org.jetbrains.kotlin:kotlin-stdlib:2.2.10", report["all_coordinates"])
        self.assertNotIn("org.jetbrains.kotlin:kotlin-stdlib:2.2.0", report["all_coordinates"])
        self.assertEqual(report["transitive_license_compliance"], "NOT VERIFIED")
        self.assertFalse(report["public_export_authorized"])
        self.assertTrue(all("--offline" in c for c in calls))
        self.assertEqual(sum(c[-1] == "debugCompileClasspath" for c in calls), 6)
        self.assertEqual(sum(c[-1] == "debugRuntimeClasspath" for c in calls), 6)
        self.assertEqual(report["plugin_classpath_and_ksp"], "NOT RUN")
        self.assertIn("INCOMPLETE", report["coverage_status"])

    def test_rejects_unresolved_report_even_exit_success(self):
        with self.assertRaisesRegex(d.Blocked, "Unresolved"):
            d.collect(self.root, "fake", self.runner([], payload="+--- fake:missing:1 FAILED"))

    def test_rejects_offline_cache_resolution_warning(self):
        with self.assertRaisesRegex(d.Blocked, "Unresolved"):
            d.collect(self.root, "fake", self.runner([], payload="Could not find org.synthetic:component:1.2"))

    def test_private_report_is_created_restricted_without_public_export(self):
        with tempfile.TemporaryDirectory() as outdir:
            output = Path(outdir) / "private-draft.json"
            snapshot = d.collect(self.root, "fake", self.runner([]))
            with patch.object(d, "collect", return_value=snapshot):
                with patch.object(sys, "argv", ["preflight",
                    "--private-checkout", str(self.root), "--private-report", str(output)]):
                    d.main()
            self.assertTrue(output.is_file())
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertFalse(__import__("json").loads(output.read_text())["public_export_authorized"])

    def test_rejects_failed_gradle_executable(self):
        with self.assertRaisesRegex(d.Blocked, "not successful"):
            d.collect(self.root, "fake", self.runner([], code=1))

    def test_rejects_wrong_public_remote(self):
        self.git("remote", "set-url", "origin", "https://github.com/ftmstr/Embasic-E-Clock-Build.git")
        with self.assertRaisesRegex(d.Blocked, "Wrong Private remote"):
            d.collect(self.root, "fake", self.runner([]))

    def test_rejects_lookalike_private_remote_before_gradle(self):
        impostors = (
            "https://github.example.invalid/ftmstr/E-Clock.git",
            "https://github.com.evil.invalid/ftmstr/E-Clock.git",
            "https://github.com/another-team/E-Clock.git",
        )
        for origin in impostors:
            with self.subTest(origin=origin):
                self.git("remote", "set-url", "origin", origin)
                with self.assertRaisesRegex(d.Blocked, "Wrong Private remote"):
                    d.collect(self.root, "fake", self.runner([]))

    def test_rejects_dirty_private_tree(self):
        (self.root / "untracked.txt").write_text("untracked")
        with self.assertRaisesRegex(d.Blocked, "Dirty"):
            d.collect(self.root, "fake", self.runner([]))

    def test_zero_phone_graph_is_not_real_dependency_inventory(self):
        with self.assertRaisesRegex(d.Blocked, "runtime graph missing"):
            d.collect(self.root, "fake", self.runner([], payload="No dependencies"))
    

if __name__ == "__main__":
    unittest.main(verbosity=2)
