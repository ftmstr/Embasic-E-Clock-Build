#!/usr/bin/env python3
"""Collect a DRAFT resolved Gradle component queue in an authorized PRIVATE clone.

This only enumerates concrete Gradle dependency-tree coordinates for later
Maven-POM/SPDX/legal review. It NEVER asserts license compliance, exports code,
publishes to GitHub or uploads an APK.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

TARGETS = (
    (":app-phone", "debugRuntimeClasspath"),
    (":app-wear", "debugRuntimeClasspath"),
    (":core:model", "debugRuntimeClasspath"),
    (":core:alarm", "debugRuntimeClasspath"),
    (":core:data", "debugRuntimeClasspath"),
    (":core:sync", "debugRuntimeClasspath"),
)
GAV = re.compile(
    r"\b(?P<group>[A-Za-z0-9_.-]+):(?P<artifact>[A-Za-z0-9_.-]+):"
    r"(?P<version>[0-9][A-Za-z0-9+_.-]*)"
)


class Blocked(Exception):
    pass


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stderr=subprocess.DEVNULL,
        text=True, timeout=60,
    ).strip()


def parse_tree(stdout: str) -> set[str]:
    if any(x in stdout for x in ("FAILED", "UNRESOLVED", "Could not resolve",
                                 "No matching variant", "FAILURE:")):
        raise Blocked("Unresolved Gradle component or configuration")
    coords: set[str] = set()
    for line in stdout.splitlines():
        if not ("--- " in line or "(c)" in line):
            continue
        matches = list(GAV.finditer(line))
        if not matches:
            continue
        match = matches[0]
        version = match["version"]
        arrow = line[match.end():].split("(*)")[0].split("(c)")[0]
        selected = re.search(r"->\s+([0-9][A-Za-z0-9+_.-]*)", arrow)
        if selected:
            version = selected[1]
        coords.add(f"{match['group']}:{match['artifact']}:{version}")
    return coords


def collect(root: Path, executable: str = "gradle", runner=None) -> dict:
    root = root.resolve(strict=True)
    try:
        if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
            raise Blocked("Select a trusted Private Git checkout root")
        if git(root, "rev-parse", "--is-shallow-repository") != "false":
            raise Blocked("Private history must be complete")
        if git(root, "branch", "--show-current") != "ci/zero-history-public-build-prep-20261017":
            raise Blocked("Wrong Private preparation branch")
        url = git(root, "remote", "get-url", "origin").removesuffix(".git")
        if not (url.endswith("/ftmstr/E-Clock") or url.endswith(":ftmstr/E-Clock")):
            raise Blocked("Wrong Private remote; never run against Public")
        if git(root, "status", "--porcelain", "--untracked-files=all"):
            raise Blocked("Dirty working tree; do not collect an unstable graph")
        sha = git(root, "rev-parse", "HEAD")
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise Blocked("Private Git verification unavailable") from exc
    if not shutil.which(executable) and runner is None:
        raise Blocked("Verified Gradle 9.6.0 executable unavailable")
    run = runner or subprocess.run
    rows = []
    union: set[str] = set()
    for module, config in TARGETS:
        try:
            result = run(
                [executable, "--no-daemon", "--offline", "--console=plain",
                 f"{module}:dependencies", "--configuration", config],
                cwd=root, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, timeout=900, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise Blocked("Gradle graph execution unavailable") from exc
        if result.returncode != 0:
            raise Blocked("Gradle graph resolution not successful; cache may be missing")
        components = parse_tree(result.stdout)
        if module in (":app-phone", ":app-wear") and not components:
            raise Blocked("Phone/Wear runtime graph missing")
        rows.append({"module": module, "configuration": config,
                     "components": sorted(components)})
        union.update(components)
    return {
        "source_commit": sha,
        "graph_status": "DRAFT ONLY (offline cached resolution; verify online and lock versions)",
        "requested_configurations": len(TARGETS),
        "unique_external_components": len(union),
        "modules": rows,
        "all_coordinates": sorted(union),
        "maven_pom_and_parent_licenses": "NOT VERIFIED",
        "transitive_license_compliance": "NOT VERIFIED",
        "source_redistribution_rights": "NOT APPROVED",
        "public_export_authorized": False,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--private-checkout", type=Path, required=True)
    p.add_argument("--gradle", default="gradle")
    p.add_argument("--private-report", type=Path, required=True)
    a = p.parse_args()
    root = a.private_checkout.resolve(strict=True)
    output = a.private_report.resolve()
    if output == root or root in output.parents or output.exists():
        raise SystemExit("NO-GO: report must be a new file outside the Private checkout")
    try:
        report = collect(root, a.gradle)
    except Blocked as exc:
        raise SystemExit("NO-GO: " + str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output.chmod(0o600)
    print("Private DRAFT dependency inventory written; Maven/POM licenses remain NOT VERIFIED.")
    print(f"Modules={report['requested_configurations']}, unique coordinates={report['unique_external_components']}; no source transferred.")


if __name__ == "__main__":
    main()
