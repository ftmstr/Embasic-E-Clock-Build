#!/usr/bin/env python3
"""Synthetic-only tests for offline Maven metadata evidence."""
import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location("pom_preflight",Path(__file__).with_name("pom_license_preflight.py"))
assert spec and spec.loader
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

POM=b"""<project xmlns="http://maven.apache.org/POM/4.0.0">
<modelVersion>4.0.0</modelVersion><groupId>org.example</groupId>
<artifactId>synthetic</artifactId><version>1.0</version>
<licenses><license><name>Apache License, Version 2.0</name>
<url>https://www.apache.org/licenses/LICENSE-2.0</url></license></licenses>
</project>"""


class PomTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.draft={"all_coordinates":["org.example:synthetic:1.0"],
                    "public_export_authorized":False,"source_commit":"synthetic"}
        self.path=p.pom_path(self.root,"org.example:synthetic:1.0")
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(POM)

    def test_metadata_evidence_never_means_license_approval(self):
        report=p.collect(self.draft,self.root)
        self.assertEqual(report["components"],1)
        self.assertEqual(report["missing_poms"],0)
        self.assertEqual(report["records"][0]["declared_licenses"][0]["name"],"Apache License, Version 2.0")
        self.assertEqual(report["records"][0]["pom_sha256"],hashlib.sha256(POM).hexdigest())
        self.assertEqual(report["transitive_license_compliance"],"NOT VERIFIED")
        self.assertFalse(report["public_export_authorized"])
        self.assertFalse(report["artifact_redistribution_approved"])

    def test_missing_pom_keeps_queue_open(self):
        self.path.unlink()
        r=p.collect(self.draft,self.root)
        self.assertEqual(r["missing_poms"],1)
        self.assertEqual(r["records"][0]["license_compliance"],"NOT VERIFIED")

    def test_pom_without_license_requires_manual_followup(self):
        self.path.write_bytes(b"<project><modelVersion>4.0.0</modelVersion><groupId>org.example</groupId><artifactId>synthetic</artifactId><version>1.0</version></project>")
        r=p.collect(self.draft,self.root)
        self.assertEqual(r["no_direct_licenses"],1)

    def test_inherited_parent_is_visible_but_not_resolved_automatically(self):
        raw=b"<project><parent><groupId>org.example</groupId><artifactId>base</artifactId><version>1.0</version></parent><artifactId>synthetic</artifactId></project>"
        self.path.write_bytes(raw)
        r=p.collect(self.draft,self.root)
        self.assertEqual(r["records"][0]["parent_pom"],"org.example:base:1.0")
        self.assertEqual(r["parent_pom_inheritance"],"NOT VERIFIED")

    def test_external_entity_or_internal_dtd_is_rejected(self):
        self.path.write_bytes(b'<!DOCTYPE project [<!ENTITY x "test">]><project><name>&x;</name></project>')
        with self.assertRaisesRegex(p.Blocked,"DTD/entity"):
            p.collect(self.draft,self.root)

    def test_untrusted_xml_namespace_cannot_impersonate_maven_pom(self):
        self.path.write_bytes(
            b'<project xmlns="https://invalid.example.test/pom">'
            b'<groupId>org.example</groupId><artifactId>synthetic</artifactId>'
            b'<version>1.0</version></project>'
        )
        with self.assertRaisesRegex(p.Blocked, "Maven project POM"):
            p.collect(self.draft, self.root)

    def test_foreign_namespace_license_claim_is_not_maven_evidence(self):
        raw = (
            b'<project xmlns="http://maven.apache.org/POM/4.0.0" '
            b'xmlns:foreign="https://invalid.example.test/claims">'
            b'<groupId>org.example</groupId><artifactId>synthetic</artifactId>'
            b'<version>1.0</version><foreign:licenses><foreign:license>'
            b'<foreign:name>Imposter License</foreign:name>'
            b'</foreign:license></foreign:licenses></project>'
        )
        self.path.write_bytes(raw)
        result = p.collect(self.draft, self.root)
        self.assertEqual(result["no_direct_licenses"], 1)
        self.assertEqual(result["records"][0]["declared_licenses"], [])
        self.assertFalse(result["artifact_redistribution_approved"])

    def test_invalid_xml_does_not_get_passed(self):
        self.path.write_bytes(b"<project>")
        with self.assertRaisesRegex(p.Blocked,"Invalid Maven"):
            p.collect(self.draft,self.root)

    def test_bad_coordinates_path_traversal_rejected(self):
        for bad in ("../secret:evil:1.0","org.example:synthetic:../../other","org.example:thing", "org.example:synthetic:1.0/"):
            with self.subTest(gav=bad),self.assertRaises(p.Blocked):
                p.pom_path(self.root,bad)

    def test_malicious_or_approved_draft_is_rejected(self):
        copy=dict(self.draft,public_export_authorized=True)
        with self.assertRaisesRegex(p.Blocked,"non-publishable"):
            p.collect(copy,self.root)
        copy=dict(self.draft,all_coordinates=["org.example:synthetic:1.0"]*2)
        with self.assertRaisesRegex(p.Blocked,"Duplicate"):
            p.collect(copy,self.root)

    def test_invalid_nontext_coordinates_fail_closed(self):
        for invalid in (None, 42, ["not", "a", "coordinate"]):
            with self.subTest(kind=type(invalid).__name__):
                draft = dict(self.draft, all_coordinates=[invalid])
                with self.assertRaisesRegex(p.Blocked, "Duplicate or malformed"):
                    p.collect(draft, self.root)

    def test_pom_with_wrong_artifact_id_cannot_supply_license_evidence(self):
        self.path.write_bytes(POM.replace(b"<artifactId>synthetic</artifactId>",
                                          b"<artifactId>unrelated</artifactId>"))
        with self.assertRaisesRegex(p.Blocked, "identity"):
            p.collect(self.draft, self.root)

    def test_pom_with_wrong_version_cannot_supply_license_evidence(self):
        self.path.write_bytes(POM.replace(b"<version>1.0</version>",
                                          b"<version>2.0</version>"))
        with self.assertRaisesRegex(p.Blocked, "identity"):
            p.collect(self.draft, self.root)

    def test_symlinked_pom_cannot_supply_license_evidence(self):
        target=self.root / "synthetic-elsewhere.pom"
        target.write_bytes(POM)
        self.path.unlink()
        self.path.symlink_to(target)
        with self.assertRaisesRegex(p.Blocked, "Symlink"):
            p.collect(self.draft, self.root)

    def test_linked_maven_version_directory_rejected(self):
        self.path.unlink()
        self.path.parent.rmdir()
        destination = self.root / "synthetic-metadata"
        destination.mkdir()
        self.path.parent.symlink_to(destination, target_is_directory=True)
        with self.assertRaisesRegex(p.Blocked, "Symlinked Maven metadata"):
            p.collect(self.draft, self.root)

    def test_linked_maven_root_is_rejected(self):
        alias = self.root / "synthetic-root-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(p.Blocked, "Symlinked Maven root"):
            p.collect(self.draft, alias)

    def test_metadata_xml_must_be_project(self):
        self.path.write_bytes(b"<settings/>")
        with self.assertRaisesRegex(p.Blocked,"Not a Maven"):
            p.collect(self.draft,self.root)


if __name__=="__main__":
    unittest.main(verbosity=2)
