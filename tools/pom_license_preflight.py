#!/usr/bin/env python3
"""Offline Maven POM license EVIDENCE queue for a locally prepared PRIVATE build.

Use alongside gradle_dependency_preflight.py. A POM license declaration is
metadata, NOT a compliance verdict. Never export source or private reports.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

COORD = re.compile(r"([A-Za-z0-9_.-]+):([A-Za-z0-9_.-]+):([0-9][A-Za-z0-9+_.-]*)\Z")


class Blocked(Exception):
    pass


def parse_pom(raw: bytes, expected: str | None = None) -> dict:
    if len(raw) > 1024 * 1024:
        raise Blocked("Oversized POM")
    if re.search(br"<!\s*(?:DOCTYPE|ENTITY)\b", raw, flags=re.I):
        raise Blocked("Unsafe XML DTD/entity in Maven POM")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise Blocked("Invalid Maven POM") from exc
    if root.tag.rsplit("}", 1)[-1] != "project":
        raise Blocked("Not a Maven project POM")
    def child(e, tag):
        for c in e:
            if c.tag.rsplit("}", 1)[-1] == tag:
                return c
        return None
    def value(e, tag):
        c = child(e, tag) if e is not None else None
        return (c.text or "").strip() if c is not None else ""
    licenses = []
    box = child(root, "licenses")
    if box is not None:
        for lic in box:
            if lic.tag.rsplit("}", 1)[-1] != "license":
                continue
            licenses.append({"name": value(lic, "name")[:300],
                             "url": value(lic, "url")[:500]})
    parent = child(root, "parent")
    parent_gav = ""
    if parent is not None:
        g, a, v = (value(parent, k) for k in ("groupId", "artifactId", "version"))
        if not all((g, a, v)) or not COORD.fullmatch(":".join((g,a,v))):
            raise Blocked("Unresolved Maven parent POM coordinate")
        parent_gav = ":".join((g,a,v))
    if expected is not None:
        # Missing group/version may legitimately inherit from a POM parent.
        # Unresolved property placeholders or mismatched coordinates must NOT
        # lend another component's copyright/license metadata to this GAV.
        gav = ":".join((
            value(root, "groupId") or value(parent, "groupId"),
            value(root, "artifactId"),
            value(root, "version") or value(parent, "version"),
        ))
        if not COORD.fullmatch(gav) or gav != expected:
            raise Blocked("Maven POM identity differs from expected resolved component")
    return {"licenses": licenses, "parent": parent_gav}


def pom_path(cache: Path, gav: str) -> Path:
    m = COORD.fullmatch(gav)
    if not m:
        raise Blocked("Invalid Gradle dependency coordinate")
    group, artifact, version = m.groups()
    if ".." in group or group.startswith(".") or ".." in artifact or ".." in version:
        raise Blocked("Unsafe Maven coordinate path")
    return cache.joinpath(*group.split("."), artifact, version, f"{artifact}-{version}.pom")


def ensure_unlinked_path(root: Path, filename: Path) -> None:
    # Reject linked intermediate Maven directories as well as linked POMs.
    # A missing file through a symlink must not masquerade as missing metadata.
    if root.is_symlink():
        raise Blocked("Symlinked Maven root")
    try:
        parts = filename.relative_to(root).parts
    except ValueError as exc:
        raise Blocked("POM path escapes Maven root") from exc
    cursor = root
    for component in parts:
        cursor = cursor / component
        if cursor.is_symlink():
            raise Blocked("Symlinked Maven metadata path")


def collect(draft: dict, pom_root: Path) -> dict:
    if not isinstance(draft, dict) or draft.get("public_export_authorized") is not False:
        raise Blocked("Expected a non-publishable Private Gradle draft")
    coordinates = draft.get("all_coordinates")
    if not isinstance(coordinates, list) or not coordinates or len(coordinates) > 5000:
        raise Blocked("Invalid or empty resolved component queue")
    if len(set(coordinates)) != len(coordinates) or not all(isinstance(c, str) for c in coordinates):
        raise Blocked("Duplicate or malformed resolved component coordinates")
    rows = []
    for gav in sorted(coordinates):
        filename = pom_path(pom_root, gav)
        ensure_unlinked_path(pom_root, filename)
        if not filename.is_file():
            rows.append({"coordinate": gav, "status": "POM NOT FOUND",
                         "license_compliance": "NOT VERIFIED"})
            continue
        if filename.is_symlink() or not filename.resolve().is_relative_to(pom_root.resolve()):
            raise Blocked("Symlink or escaping Maven metadata")
        raw = filename.read_bytes()
        meta = parse_pom(raw, expected=gav)
        rows.append({"coordinate": gav, "status": "POM REVIEW NEEDED",
                     "pom_sha256": hashlib.sha256(raw).hexdigest(),
                     "declared_licenses": meta["licenses"],
                     "parent_pom": meta["parent"],
                     "license_compliance": "NOT VERIFIED"})
    missing = sum(r["status"] == "POM NOT FOUND" for r in rows)
    unknown = sum(r.get("status") == "POM REVIEW NEEDED" and not r["declared_licenses"] for r in rows)
    return {"source_commit": draft.get("source_commit", "NOT VERIFIED"),
            "components": len(rows), "missing_poms": missing,
            "no_direct_licenses": unknown, "records": rows,
            "parent_pom_inheritance": "NOT VERIFIED",
            "notice_attribution": "NOT VERIFIED",
            "artifact_redistribution_approved": False,
            "transitive_license_compliance": "NOT VERIFIED",
            "public_export_authorized": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--private-draft", required=True, type=Path)
    p.add_argument("--pom-root", required=True, type=Path)
    p.add_argument("--private-report", required=True, type=Path)
    args=p.parse_args()
    if not args.private_draft.is_file() or not args.pom_root.is_dir():
        raise SystemExit("NO-GO: private draft/POM directory unavailable")
    report_path=args.private_report.resolve()
    if report_path.exists() or report_path.is_relative_to(Path.cwd().resolve()):
        raise SystemExit("NO-GO: write a fresh private report outside the current checkout")
    try:
        report=collect(json.loads(args.private_draft.read_text(encoding="utf-8")),
                       args.pom_root)
    except (ValueError, OSError, Blocked) as exc:
        raise SystemExit("NO-GO: offline POM collection failed or metadata is unsafe") from exc
    flags=os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd=os.open(report_path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(report, output, indent=2, sort_keys=True)
        output.write("\n")
    print(f"Private POM queue created: {report['components']} coordinates, "
          f"{report['missing_poms']} missing POMs. License rights NOT VERIFIED.")


if __name__ == "__main__":
    main()
