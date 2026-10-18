#!/usr/bin/env python3
"""Public, synthetic-only regression tests; never access the private E-Clock repo."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).with_name("verify_snapshot.py")
spec = importlib.util.spec_from_file_location("verify_snapshot", SOURCE)
assert spec and spec.loader
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Synthetic CI")
        self.git("config", "user.email", "fixture@example.invalid")
        self.write("README.md", "Synthetic fixture only\n")
        self.git("add", ".")
        self.git("commit", "-m", "public synthetic bootstrap")
        self.expected_root = self.git("rev-parse", "HEAD").strip()
        for name in sorted(v.INFRA_FILES - {"README.md"}):
            self.write(name, "# synthetic infrastructure\n")
        self.git("add", ".")
        self.git("commit", "-m", "public fixture tools")
        names = sorted(v.REQUIRED) + [f"core/model/src/test/java/Synthetic{n:02d}.kt" for n in range(13)]
        for name in names:
            self.write(name, "// synthetic, no private application code\n")
        self.git("add", ".")
        self.git("commit", "-m", "synthetic reviewed source")
        self.make_audit()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.DEVNULL).decode()

    def write(self, path, content):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            dest.write_bytes(content)
        else:
            dest.write_text(content, encoding="utf-8")

    def tracked(self):
        return sorted(p for p in self.git("ls-files").splitlines() if p)

    def make_audit(self, **overrides):
        tracked = self.tracked()
        sources = sorted(set(tracked) - v.INFRA_FILES - {v.AUDIT_FILE})
        public = sorted(set(tracked) - {v.AUDIT_FILE})
        audit = dict(v.CLAIMS)
        audit.update({
            "source_files": sources,
            "source_inventory_sha256": v.digest(self.root, sources),
            "public_inventory_sha256": v.digest(self.root, public),
            "reviewed_asset_sha256": {},
        })
        audit.update(overrides)
        self.write(v.AUDIT_FILE, json.dumps(audit) + "\n")
        self.git("add", v.AUDIT_FILE)
        self.git("commit", "-m", "synthetic audit claim")
        return audit

    def check(self, approval=None):
        audit = json.loads((self.root / v.AUDIT_FILE).read_text())
        if approval is None:
            approval = v.approval_seal(self.root, audit["public_inventory_sha256"])
        return v.verify(self.root, expected_root=self.expected_root, approved=approval)

    def test_multi_commit_public_history_with_known_root_passes_synthetic_contract(self):
        got = self.check()
        self.assertGreaterEqual(got["sources"], 20)
        self.assertEqual(got["approved_digest"], v.approval_seal(self.root, json.loads((self.root/v.AUDIT_FILE).read_text())["public_inventory_sha256"]))

    def test_no_out_of_band_admin_digest_blocks_even_approved_json(self):
        with self.assertRaisesRegex(v.Blocked, "admin-managed"):
            self.check(approval="")

    def test_wrong_out_of_band_digest_blocks(self):
        with self.assertRaisesRegex(v.Blocked, "admin-managed"):
            self.check(approval="f" * 64)

    def test_approval_seal_binds_audit_claims_even_when_source_is_unchanged(self):
        prior = self.check()["approved_digest"]
        audit = json.loads((self.root / v.AUDIT_FILE).read_text())
        audit["source_rights_approved"] = "NOT APPROVED"
        self.write(v.AUDIT_FILE, json.dumps(audit) + "\n")
        self.assertNotEqual(prior, v.approval_seal(self.root, audit["public_inventory_sha256"]))
        with self.assertRaises(v.Blocked):
            self.check(approval=prior)

    def test_no_private_human_and_license_review_blocks(self):
        self.make_audit(source_rights_approved="NOT REVIEWED")
        with self.assertRaisesRegex(v.Blocked, "Private scan"):
            self.check()

    def test_public_workflow_modified_after_approval_blocks(self):
        self.write(".github/workflows/android-ci.yml", "# tampered synthetic CI\n")
        with self.assertRaisesRegex(v.Blocked, "Public infrastructure"):
            self.check()

    def test_binary_asset_missing_explicit_rights_hash_blocks(self):
        path = "app-phone/src/main/res/drawable/synthetic.png"
        self.write(path, b"\x89PNG\r\n\x1a\nsynthetic")
        self.git("add", ".")
        self.git("commit", "-m", "new synthetic graphic")
        self.make_audit()
        with self.assertRaisesRegex(v.Blocked, "asset review"):
            self.check()

    def test_unapproved_secret_or_signing_file_blocks_even_with_updated_manifest(self):
        self.write("app-phone/src/main/secrets.properties", "synthetic_secret=not_a_secret\n")
        self.git("add", ".")
        self.git("commit", "-m", "synthetic forbidden file")
        with self.assertRaisesRegex(v.Blocked, "Unapproved path"):
            self.check()

    def test_symlink_is_rejected(self):
        (self.root / "app-phone/src/main/alias.kt").symlink_to("AndroidManifest.xml")
        self.git("add", "app-phone/src/main/alias.kt")
        self.git("commit", "-m", "synthetic symlink")
        with self.assertRaisesRegex(v.Blocked, "Unapproved path"):
            self.check()

    def test_imported_unrelated_git_history_is_rejected(self):
        with self.assertRaisesRegex(v.Blocked, "Unexpected Git root"):
            v.verify(self.root, expected_root="0" * 40, approved="f" * 64)

    def test_revision_in_source_requires_new_admin_digest_and_manifest(self):
        self.write("core/model/src/test/java/Synthetic01.kt", "// modified synthetic source\n")
        with self.assertRaisesRegex(v.Blocked, "Private exporter/source inventory"):
            self.check()

    def test_private_old_one_commit_policy_is_incompatible_with_public_bootstrap(self):
        self.assertGreater(int(self.git("rev-list", "--all", "--count")), 1)
        self.assertEqual(len(self.git("rev-list", "--all", "--max-parents=0").splitlines()), 1)

    def test_source_paths_deny_unexpected_dirs(self):
        self.assertFalse(v.safe_path("docs/private_notes.md"))
        self.assertFalse(v.safe_path("app-phone/src/../../outside.kt"))
        self.assertFalse(v.safe_path("core/model/src/foo.jar"))
        self.assertTrue(v.safe_path("app-wear/src/main/java/com/example/Fake.kt"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
