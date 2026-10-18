#!/usr/bin/env python3
"""Synthetic full-history regression cases; does not inspect Private code."""
from __future__ import annotations
import subprocess
import tempfile
import unittest
from pathlib import Path
import audit_public_git_history as h


class PublicHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run_git("init", "-b", "main")
        self.run_git("config", "user.name", "Synthetic")
        self.run_git("config", "user.email", "synthetic@example.invalid")
        self.write("README.md", "benign test content")
        self.commit("synthetic public root")
        self.trusted = self.run_git("rev-parse", "HEAD").strip()

    def run_git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.DEVNULL, text=True)

    def write(self, name, content):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def commit(self, message):
        self.run_git("add", "-A")
        self.run_git("commit", "-m", message)

    def scan(self):
        return h.inspect(self.root, self.trusted)

    def test_clean_multiple_public_commits_pass(self):
        self.write(".gitignore", "synthetic")
        self.commit("synthetic second")
        r = self.scan()
        self.assertEqual(r["commits"], 2)
        self.assertGreaterEqual(r["unique_blobs"], 2)

    def test_removed_private_path_from_history_is_rejected(self):
        self.write("private/SyntheticSecret.txt", "safe text")
        self.commit("temporary wrong path")
        (self.root / "private/SyntheticSecret.txt").unlink()
        self.commit("remove wrong path")
        with self.assertRaisesRegex(h.Blocked, "historical path"):
            self.scan()

    def test_removed_dummy_credential_from_historical_blob_is_rejected(self):
        self.write("README.md", "ghp_" + "z" * 28)
        self.commit("synthetic dummy credential")
        self.write("README.md", "cleaned")
        self.commit("removed synthetic dummy credential")
        with self.assertRaisesRegex(h.Blocked, "Potential historical credential"):
            self.scan()

    def test_removed_symlink_is_still_rejected(self):
        (self.root / ".gitignore").symlink_to("README.md")
        self.commit("synthetic link")
        (self.root / ".gitignore").unlink()
        self.commit("removed synthetic link")
        with self.assertRaisesRegex(h.Blocked, "Git link"):
            self.scan()

    def test_historical_commit_message_dummy_token_is_rejected(self):
        self.write("README.md", "no secret")
        self.commit("ghp_" + "z" * 28)
        with self.assertRaisesRegex(h.Blocked, "commit message"):
            self.scan()

    def test_non_git_root_or_missing_history_rejected(self):
        with self.assertRaisesRegex(h.Blocked, "unexpected root"):
            h.inspect(self.root, "0" * 40)

    def test_hidden_wrong_extension_in_historical_tree_rejected(self):
        self.write("app-phone/src/main/Fake.secret", "synthetic")
        self.commit("wrong extension")
        (self.root / "app-phone/src/main/Fake.secret").unlink()
        self.commit("remove")
        with self.assertRaisesRegex(h.Blocked, "historical path"):
            self.scan()


if __name__ == "__main__":
    unittest.main(verbosity=2)
