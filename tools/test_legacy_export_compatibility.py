#!/usr/bin/env python3
"""Synthetic-only regressions for legacy snapshot handoff."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location(
    "legacy_export",Path(__file__).with_name("legacy_export_compatibility.py"))
assert spec and spec.loader
x=importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)

class LegacyContractTests(unittest.TestCase):
    def setUp(self):
        self.paths=sorted(set(x.REQUIRED)|{f"core/model/src/test/java/Synthetic{i:02d}.kt"
                                           for i in range(12)}|x.LEGACY_METADATA)
        self.audit={
            "files":len(self.paths),"inventory_sha256":"e"*64,
            "zero_git_history":True,"automated_secret_scan":"PASS",
            "public_approval":"HUMAN REVIEW REQUIRED",
            "private_issue_pr_actions_history_review":"NOT VERIFIED",
            "actual_android_build":"NOT RUN",
        }

    def test_legacy_export_is_never_auto_approved(self):
        got=x.assess(self.audit,self.paths)
        self.assertEqual(got["status"],"NO-GO")
        self.assertFalse(got["publication_authorized"])
        self.assertEqual(got["source_bytes_examined"],0)
        self.assertIn("UNSAFE_LEGACY_WORKFLOW",got["reason_codes"])
        self.assertIn("PUBLIC_SOURCE_MANIFEST_ABSENT",got["reason_codes"])

    def test_forged_all_approved_legacy_export_still_blocked(self):
        fake={**self.audit, "public_approval":"APPROVED",
              "private_issue_pr_actions_history_review":"VERIFIED",
              "source_files":[],"source_inventory_sha256":"0"*64,
              "public_inventory_sha256":"0"*64,"reviewed_asset_sha256":{},
              "source_rights_approved":"APPROVED",
              "artifact_redistribution_approved":"APPROVED",
              "private_history_audit":"VERIFIED"}
        got=x.assess(fake,self.paths)
        self.assertFalse(got["publication_authorized"])
        self.assertIn("REQUIRES_INDEPENDENT_PUBLIC_APPROVAL_SEAL",got["reason_codes"])
        self.assertIn("SOURCE_BYTES_NOT_INSPECTED",got["reason_codes"])

    def test_bad_count_always_blocks(self):
        got=x.assess({**self.audit,"files":999},self.paths)
        self.assertIn("LEGACY_COUNT_MISMATCH",got["reason_codes"])

    def test_duplicate_and_case_collision_blocks(self):
        got=x.assess(self.audit,self.paths+["README.md","readme.md"])
        self.assertIn("DUPLICATE_OR_CASE_COLLISION",got["reason_codes"])

    def test_forbidden_public_filename_blocks(self):
        got=x.assess(self.audit,self.paths+["app-phone/src/main/secrets.properties"])
        self.assertIn("PUBLIC_PATH_ALLOWLIST_MISMATCH",got["reason_codes"])

    def test_missing_android_modules_blocks(self):
        got=x.assess(self.audit,["README.md","SNAPSHOT-AUDIT.json"])
        self.assertIn("MANDATORY_ANDROID_SOURCES_MISSING",got["reason_codes"])

    def test_folder_analysis_does_not_read_source_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in self.paths:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
                if name=="SNAPSHOT-AUDIT.json":
                    p.write_text(json.dumps(self.audit),encoding="utf-8")
                else:
                    p.write_text("synthetic fixture only",encoding="utf-8")
            res=x.analyze_folder(root)
            self.assertEqual(res["source_bytes_examined"],0)
            self.assertFalse(res["publication_authorized"])
            # Any tool CLI invocation exits nonzero, even for correct legacy inputs.
            with patch("sys.argv",["legacy","--local-legacy-export",str(root)]):
                with self.assertRaises(SystemExit) as cm:
                    x.main()
                self.assertEqual(cm.exception.code,2)

    def test_symlink_export_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"SNAPSHOT-AUDIT.json").write_text(json.dumps(self.audit))
            (root/"fake.kt").symlink_to("SNAPSHOT-AUDIT.json")
            with self.assertRaisesRegex(ValueError,"symlink"):
                x.analyze_folder(root)

    def test_invalid_manifest_is_blocked(self):
        got=x.assess("not a dict",self.paths)
        self.assertEqual(got["reason_codes"],["INVALID_LEGACY_MANIFEST"])


if __name__=="__main__":
    unittest.main(verbosity=2)
