#!/usr/bin/env python3
"""Non-publishing compatibility audit for Private legacy E-Clock exports.

Only examines the *manifest* and filenames in an isolated local review folder.
Never copies source, creates Public approval, or pushes Git commits. A clean
legacy exporter report is NOT equivalent to the newer Public security seal.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from verify_snapshot import REQUIRED, SOURCE_FILES, safe_path

LEGACY_WORKFLOW = ".github/workflows/public-snapshot-android.yml"
LEGACY_METADATA = {"README.md", "SNAPSHOT-AUDIT.json", LEGACY_WORKFLOW}
EXPECTED_LEGACY_FIELDS = {
    "files", "inventory_sha256", "zero_git_history",
    "automated_secret_scan", "public_approval",
    "private_issue_pr_actions_history_review", "actual_android_build",
}


def assess(audit: object, paths: list[str]) -> dict[str, object]:
    """Return status *codes*, never private paths/content. Always NO-GO."""
    reasons: set[str] = set()
    if not isinstance(audit, dict):
        return {"status": "NO-GO", "reason_codes": ["INVALID_LEGACY_MANIFEST"],
                "candidate_source_count": 0, "publication_authorized": False}
    if not EXPECTED_LEGACY_FIELDS.issubset(audit):
        reasons.add("LEGACY_SCHEMA_INCOMPLETE")
    if audit.get("zero_git_history") is not True:
        reasons.add("LEGACY_ZERO_HISTORY_NOT_ATTESTED")
    if audit.get("automated_secret_scan") != "PASS":
        reasons.add("LEGACY_STRICT_SCAN_NOT_PASS")
    if audit.get("public_approval") != "APPROVED":
        reasons.add("LEGACY_HUMAN_APPROVAL_MISSING")
    if audit.get("private_issue_pr_actions_history_review") != "VERIFIED":
        reasons.add("HISTORY_METADATA_REVIEW_MISSING")
    if not isinstance(paths, list) or any(not isinstance(p, str) for p in paths):
        paths = []
        reasons.add("INVALID_FILE_LIST")
    if len(paths) != len(set(paths)) or len({p.casefold() for p in paths}) != len(paths):
        reasons.add("DUPLICATE_OR_CASE_COLLISION")
    if not paths or audit.get("files") != len(paths):
        reasons.add("LEGACY_COUNT_MISMATCH")
    if LEGACY_WORKFLOW in paths:
        reasons.add("UNSAFE_LEGACY_WORKFLOW")
        # Legacy exporter ROOT_FILES requires .yml, but its ALLOWED_SUFFIXES
        # omits .yml, so check_name() rejects its own mandatory workflow.
        reasons.add("LEGACY_REQUIRED_YAML_REJECTED_BY_EXPORTER")
    if any(p.startswith((".git/", ".github/workflows/")) and p != LEGACY_WORKFLOW
           for p in paths):
        reasons.add("UNEXPECTED_GIT_OR_WORKFLOW")
    if any(p not in LEGACY_METADATA and not safe_path(p) for p in paths):
        reasons.add("PUBLIC_PATH_ALLOWLIST_MISMATCH")
    candidate = sorted(set(paths) - LEGACY_METADATA)
    if not REQUIRED.issubset(candidate) or len(candidate) < 20:
        reasons.add("MANDATORY_ANDROID_SOURCES_MISSING")
    if audit.get("source_files") is None:
        reasons.add("PUBLIC_SOURCE_MANIFEST_ABSENT")
    if audit.get("source_inventory_sha256") is None:
        reasons.add("PUBLIC_SOURCE_SHA256_ABSENT")
    if audit.get("public_inventory_sha256") is None:
        reasons.add("PUBLIC_WORKFLOW_AND_SOURCE_SHA256_ABSENT")
    if audit.get("reviewed_asset_sha256") is None:
        reasons.add("ASSET_RIGHTS_EVIDENCE_ABSENT")
    if audit.get("source_rights_approved") != "APPROVED":
        reasons.add("SOURCE_RIGHTS_UNVERIFIED")
    if audit.get("artifact_redistribution_approved") != "APPROVED":
        reasons.add("ARTIFACT_RIGHTS_UNVERIFIED")
    if audit.get("private_history_audit") != "VERIFIED":
        reasons.add("PRIVATE_FULL_HISTORY_NOT_ATTESTED")
    # The exporter does not seal the full current public workflow and root.
    reasons.add("REQUIRES_INDEPENDENT_PUBLIC_APPROVAL_SEAL")
    reasons.add("REQUIRES_PROTECTED_PUBLIC_MAIN")
    # Manifest-only inputs can never prove file bytes, rights, or Gitleaks.
    reasons.add("SOURCE_BYTES_NOT_INSPECTED")
    return {
        "status": "NO-GO",
        "reason_codes": sorted(reasons),
        "candidate_source_count": len(candidate),
        "publication_authorized": False,
        "source_bytes_examined": 0,
    }


def analyze_folder(folder: Path) -> dict[str, object]:
    # This operation MUST be run only on an already existing, local Private
    # staging directory. Do not point it at Public or auto-discover any source.
    folder = folder.resolve(strict=True)
    audit_path = folder / "SNAPSHOT-AUDIT.json"
    if not audit_path.is_file() or audit_path.is_symlink():
        raise ValueError("Legacy audit file absent or linked")
    if audit_path.stat().st_size > 1024 * 1024:
        raise ValueError("Unreasonably large legacy audit")
    # Neither follow symlinks nor read source-file contents.
    paths = []
    for f in folder.rglob("*"):
        if f.is_symlink():
            raise ValueError("Legacy export contains symlink")
        if f.is_file():
            paths.append(f.relative_to(folder).as_posix())
    data = json.loads(audit_path.read_text(encoding="utf-8"))
    return assess(data, paths)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-legacy-export", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = analyze_folder(args.local_legacy_export)
    except (OSError, ValueError) as exc:
        raise SystemExit("NO-GO: legacy export cannot be inspected safely") from exc
    print(json.dumps(result, indent=2))
    raise SystemExit(2)  # Audit tool NEVER authorizes upload/build.


if __name__ == "__main__":
    main()
