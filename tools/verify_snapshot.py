#!/usr/bin/env python3
"""Fail-closed verifier for a reviewed E-Clock PUBLIC source snapshot.

This checker cannot perform a private Gitleaks/license audit. The repository
administrator must set ECLOCK_APPROVED_PUBLIC_SHA256 after independent review.
Never infer approval from a JSON file checked into this repository alone.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

PUBLIC_ROOT = "9ba88a5482e30ddb3834e79dede8240af13185c3"
SOURCE_ROOTS = ("app-phone/", "app-wear/", "core/model/", "core/alarm/", "core/data/", "core/sync/")
SOURCE_FILES = {"settings.gradle.kts", "build.gradle.kts", "gradle.properties", "gradle/libs.versions.toml"}
REQUIRED = SOURCE_FILES | {"app-phone/build.gradle.kts", "app-wear/build.gradle.kts", "core/model/build.gradle.kts", "core/alarm/build.gradle.kts", "core/data/build.gradle.kts", "core/sync/build.gradle.kts", "app-phone/src/main/AndroidManifest.xml", "app-wear/src/main/AndroidManifest.xml"}
INFRA_FILES = {"README.md", ".gitignore", ".github/workflows/android-ci.yml", "tools/verify_snapshot.py", "tools/test_verify_snapshot.py", "docs/PUBLIC_SNAPSHOT_HANDOFF.md"}
AUDIT_FILE = "SNAPSHOT-AUDIT.json"
BAD_NAMES = {"local.properties", "google-services.json", "secrets.properties", "credentials.json", "keystore.properties", ".env", ".gitmodules", "gradle-wrapper.jar"}
BAD_SUFFIXES = {".jks", ".keystore", ".p12", ".pfx", ".pem", ".key", ".sqlite", ".db", ".log", ".apk", ".aab", ".zip", ".jar", ".udf", ".mp3", ".wav", ".cer", ".crt"}
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".ttf", ".otf", ".svg"}
SOURCE_SUFFIXES = {".kt", ".java", ".xml", ".kts", ".toml", ".properties", ".pro", ".txt", ".json"} | ASSET_SUFFIXES
CLAIMS = {
    "automated_secret_scan": "PASS",
    "private_history_audit": "VERIFIED",
    "source_rights_approved": "APPROVED",
    "artifact_redistribution_approved": "APPROVED",
    "public_approval": "APPROVED",
}


class Blocked(Exception):
    """An unmet security invariant, never a build or test failure."""


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.DEVNULL)


def digest(root: Path, paths: list[str]) -> str:
    rows = [hashlib.sha256((root / p).read_bytes()).hexdigest() + "  " + p for p in paths]
    return hashlib.sha256(("\n".join(sorted(rows)) + "\n").encode()).hexdigest()


def approval_seal(root: Path, public_digest: str) -> str:
    """Admin approves BOTH immutable tracked bytes and audit JSON assertions."""
    audit_hash = hashlib.sha256((root / AUDIT_FILE).read_bytes()).hexdigest()
    return hashlib.sha256((public_digest + "\n" + audit_hash + "\n").encode()).hexdigest()


def source_path(path: str) -> bool:
    if path in SOURCE_FILES:
        return True
    if not path.startswith(SOURCE_ROOTS):
        return False
    bits = PurePosixPath(path).parts
    if len(bits) < 2:
        return False
    if path.endswith("/build.gradle.kts") and len(bits) in (2, 3):
        return True
    return ("src" in bits or "schemas" in bits or bits[-1] == "consumer-rules.pro") and PurePosixPath(path).suffix.lower() in SOURCE_SUFFIXES


def safe_path(path: str) -> bool:
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", path):
        return False
    bits = PurePosixPath(path).parts
    if not bits or any(x in (".", "..", ".git", ".gradle", ".idea", "build", "test-results", "reports") for x in bits):
        return False
    if any(x.lower() in {"private", "raporlar", "yedekleme"} for x in bits):
        return False
    p = PurePosixPath(path)
    if p.name.lower() in BAD_NAMES or p.suffix.lower() in BAD_SUFFIXES:
        return False
    return path in INFRA_FILES or path == AUDIT_FILE or source_path(path)


def verify(root: Path, expected_root: str = PUBLIC_ROOT, approved: str = "") -> dict[str, int | str]:
    root = root.resolve()
    try:
        if git(root, "rev-parse", "--is-shallow-repository").strip() != b"false":
            raise Blocked("Shallow history cannot establish provenance")
        roots = git(root, "rev-list", "--all", "--max-parents=0").decode().splitlines()
        if roots != [expected_root]:
            raise Blocked("Unexpected Git root or imported ancestry")
        refs = git(root, "for-each-ref", "--format=%(refname)", "refs/remotes/origin", "refs/heads").decode().splitlines()
        if set(refs) - {"refs/remotes/origin/HEAD", "refs/remotes/origin/main", "refs/heads/main"}:
            raise Blocked("Unexpected branch or ref")
        if git(root, "tag", "--list").strip():
            raise Blocked("Unexpected tags")
        index = git(root, "ls-files", "--stage", "-z")
    except (subprocess.CalledProcessError, OSError, UnicodeError) as exc:
        raise Blocked("Unable to audit complete Git index and history") from exc
    tracked: list[str] = []
    for entry in index.split(b"\0"):
        if not entry:
            continue
        try:
            metadata, name = entry.split(b"\t", 1)
            mode = metadata.split()[0]
            path = name.decode("utf-8", "strict")
        except (ValueError, UnicodeError) as exc:
            raise Blocked("Malformed index entry") from exc
        if mode not in (b"100644", b"100755") or not safe_path(path):
            raise Blocked("Unapproved path, file mode, or file type")
        if (root / path).stat().st_size > 5 * 1024 * 1024:
            raise Blocked("Unreviewed oversized file")
        tracked.append(path)
    if len(tracked) != len(set(tracked)) or len({p.casefold() for p in tracked}) != len(tracked):
        raise Blocked("Duplicate or case-conflicting tracked paths")
    tracked_set = set(tracked)
    if not INFRA_FILES.issubset(tracked_set) or AUDIT_FILE not in tracked_set:
        raise Blocked("Missing public infrastructure or audit document")
    sources = sorted(tracked_set - INFRA_FILES - {AUDIT_FILE})
    if not REQUIRED.issubset(sources) or len(sources) < 20:
        raise Blocked("Incomplete Android/Wear source snapshot")
    try:
        audit = json.loads((root / AUDIT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Blocked("Missing or invalid private audit attestation") from exc
    if not isinstance(audit, dict) or any(audit.get(k) != v for k, v in CLAIMS.items()):
        raise Blocked("Private scan, history, IP or publication review is not approved")
    if audit.get("source_files") != sources or audit.get("source_inventory_sha256") != digest(root, sources):
        raise Blocked("Private exporter/source inventory contract does not match")
    public_paths = sorted(tracked_set - {AUDIT_FILE})
    tree_digest = digest(root, public_paths)
    if audit.get("public_inventory_sha256") != tree_digest:
        raise Blocked("Public infrastructure/source inventory differs from reviewed content")
    if not re.fullmatch(r"[a-f0-9]{64}", approved) or approved != approval_seal(root, tree_digest):
        raise Blocked("Independent admin-managed SHA-256 approval missing or mismatched")
    assets = {p for p in sources if PurePosixPath(p).suffix.lower() in ASSET_SUFFIXES}
    asset_hashes = audit.get("reviewed_asset_sha256")
    if not isinstance(asset_hashes, dict) or set(asset_hashes) != assets:
        raise Blocked("Binary/vector asset review missing")
    if any(asset_hashes[p] != hashlib.sha256((root / p).read_bytes()).hexdigest() for p in assets):
        raise Blocked("Asset hash changed since rights review")
    return {"sources": len(sources), "tracked": len(tracked), "approved_digest": approval_seal(root, tree_digest)}


def main() -> None:
    # This runs on *public* sources only. Audit values never imply private scanning ran.
    try:
        result = verify(Path.cwd(), approved=os.getenv("ECLOCK_APPROVED_PUBLIC_SHA256", ""))
    except Blocked as exc:
        raise SystemExit(f"NO-GO: {exc}") from exc
    print(f"Source audit gate PASS: {result['sources']} source files; approved public inventory digest")


if __name__ == "__main__":
    main()
