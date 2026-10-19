#!/usr/bin/env python3
"""Fail-closed workflow policy regression: PR checks without APK permission."""
from pathlib import Path
import re
import unittest

FLOW=Path(__file__).resolve().parents[1]/".github/workflows/android-ci.yml"


class WorkflowContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flow=FLOW.read_text(encoding="utf-8")

    def test_public_pr_event_and_push_main_both_trigger(self):
        self.assertIn("  pull_request:\n    branches: [main]",self.flow)
        self.assertIn("  push:\n    branches: [main]",self.flow)

    def test_bootstrap_synthetic_check_runs_for_main_pr_and_push(self):
        s=self.flow.split("  bootstrap-tests:",1)[1].split("  source-audit:",1)[0]
        self.assertIn("github.event_name == 'pull_request'",s)
        self.assertIn("github.base_ref == 'main'",s)
        self.assertIn("python3 -m unittest discover",s)
        self.assertIn("python3 tools/audit_public_git_history.py",s)
        self.assertIn("fetch-depth: 0",s)

    def test_private_source_audit_never_runs_on_untrusted_pr(self):
        s=self.flow.split("  source-audit:",1)[1].split("\n  build:",1)[0]
        self.assertIn("needs: bootstrap-tests",s)
        self.assertIn("github.ref == 'refs/heads/main'",s)
        self.assertIn("python3 tools/check_branch_protection.py",s)
        self.assertIn("python3 tools/verify_snapshot.py",s)
        self.assertLess(s.index("check_branch_protection.py"),s.index("verify_snapshot.py"))

    def test_debug_build_requires_source_audit_and_fails_closed(self):
        s=self.flow.split("\n  build:",1)[1]
        self.assertIn("needs: source-audit",s)
        self.assertIn("target: [core, phone, wear]",s)
        self.assertIn("retention-days: 3",s)
        self.assertIn("if: success() && matrix.target != 'core'",s)
        self.assertNotIn("pull_request_target:",self.flow)
        self.assertNotIn("runs-on: self-hosted",self.flow)

    def test_checkout_pins_and_minimal_permissions(self):
        self.assertIn("permissions:\n  contents: read",self.flow)
        pins=re.findall(r"uses: (actions/[\w-]+)@([a-z0-9]+)",self.flow)
        self.assertGreaterEqual(len(pins),4)
        self.assertTrue(all(re.fullmatch(r"[a-f0-9]{40}",rev) for name,rev in pins))
        self.assertGreaterEqual(self.flow.count("persist-credentials: false"),3)


if __name__=="__main__":
    unittest.main(verbosity=2)
