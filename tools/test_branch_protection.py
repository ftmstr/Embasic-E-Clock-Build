#!/usr/bin/env python3
"""Synthetic read-only branch policy checks; never change live GitHub settings."""
from __future__ import annotations
import importlib.util
import io
import json
from pathlib import Path
import unittest
from urllib.error import URLError

path=Path(__file__).with_name("check_branch_protection.py")
spec=importlib.util.spec_from_file_location("branch_policy", path)
assert spec and spec.loader
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class FakeReply:
    def __init__(self, data, status=200):
        self.status=status
        self.data=json.dumps(data).encode() if not isinstance(data, bytes) else data
    def read(self, n): return self.data[:n]
    def __enter__(self): return self
    def __exit__(self, *_): return False


class PolicyTests(unittest.TestCase):
    def read(self, data, status=200, fail=False, repository=p.EXPECTED):
        def fake(request, timeout):
            self.assertEqual(timeout, 15)
            self.assertEqual(request.full_url,
                             "https://api.github.com/repos/ftmstr/Embasic-E-Clock-Build/branches/main")
            if fail:
                raise URLError("synthetic unavailable")
            return FakeReply(data, status)
        return p.check(repo=repository, opener=fake, token="")

    def test_unprotected_main_is_blocked(self):
        with self.assertRaisesRegex(p.PolicyBlocked, "NOT PROTECTED"):
            self.read({"name": "main", "protected": False})

    def test_protected_boolean_never_claims_reviewed_rules(self):
        result=self.read({"name": "main", "protected": True})
        self.assertTrue(result["protected"])
        self.assertIn("NOT VERIFIED", result["rule_details"])

    def test_wrong_branch_name_is_blocked(self):
        with self.assertRaisesRegex(p.PolicyBlocked, "not for main"):
            self.read({"name": "dev", "protected": True})

    def test_wrong_repository_is_blocked_before_network_request(self):
        with self.assertRaisesRegex(p.PolicyBlocked, "Unexpected repository"):
            p.check("ftmstr/E-Clock", opener=lambda *a, **k: self.fail("wrong repo"))

    def test_http_error_or_unreachable_network_is_blocked(self):
        with self.assertRaisesRegex(p.PolicyBlocked, "readback failed"):
            self.read({"name": "main", "protected": True}, status=403)
        with self.assertRaisesRegex(p.PolicyBlocked, "unreachable"):
            self.read({}, fail=True)

    def test_empty_or_invalid_response_is_blocked(self):
        with self.assertRaisesRegex(p.PolicyBlocked, "response invalid"):
            self.read(b"{ invalid")
        with self.assertRaisesRegex(p.PolicyBlocked, "not for main"):
            self.read({"protected": True})


if __name__ == "__main__":
    unittest.main(verbosity=2)
