#!/usr/bin/env python3
"""PRIVATE-CHECKOUT-ONLY security preflight. Does not copy or publish code.

This is a narrow automation of Gitleaks and Git hygiene, NOT license/PII/legal
approval or a replacement for PR/issue/Actions-log review. Keep output private.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess

EXPECTED_PRIVATE = "E-Clock"
PUBLIC_NAME = "Embasic-E-Clock-Build"


class NoGo(Exception):
    pass


def git(folder: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(folder), *args],
        stderr=subprocess.DEVNULL, text=True, timeout=60,
    ).strip()


def scan(folder: Path, *, executable: str | None = None, invoke=None) -> dict:
    """May run only against a clean, complete trusted local Private clone.

    No secret contents, local filesystem path, identifiers or scan logs are
    returned, printed or written. Nonzero scanner exit is always a blocker.
    """
    folder = folder.resolve(strict=True)
    if not folder.is_dir():
        raise NoGo("Local Private Git checkout is not a directory")
    try:
        if Path(git(folder, "rev-parse", "--show-toplevel")).resolve() != folder:
            raise NoGo("Select the Private checkout root, not a subdirectory")
        if git(folder, "rev-parse", "--is-shallow-repository") != "false":
            raise NoGo("Private clone is shallow; full history is required")
        if git(folder, "status", "--porcelain", "--untracked-files=all"):
            raise NoGo("Private checkout must be clean, including untracked files")
        if git(folder, "branch", "--show-current") != "ci/zero-history-public-build-prep-20261017":
            raise NoGo("Use the exact dedicated Private preparation branch")
        remote = git(folder, "remote", "get-url", "origin")
        normalized = remote.removesuffix(".git").rstrip("/")
        if PUBLIC_NAME in normalized or not normalized.endswith("/ftmstr/" + EXPECTED_PRIVATE) and not normalized.endswith(":ftmstr/" + EXPECTED_PRIVATE):
            raise NoGo("Remote is not the expected Private E-Clock source")
        refs = git(folder, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes", "refs/tags").splitlines()
        if not refs:
            raise NoGo("Missing Git refs")
        count = int(git(folder, "rev-list", "--all", "--count"))
        if count < 1:
            raise NoGo("No traversable Git history")
    except (subprocess.CalledProcessError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise NoGo("Private Git provenance inspection failed") from exc

    tool = executable if executable is not None else shutil.which("gitleaks")
    if not tool:
        raise NoGo("Gitleaks executable missing; strict scan NOT RUN")
    caller = invoke if invoke is not None else subprocess.run
    scans = (
        ["git", "--no-banner", "--redact", "--log-opts=--all", str(folder)],
        ["dir", "--no-banner", "--redact", str(folder)],
    )
    for subcommand in scans:
        try:
            result = caller(
                [tool, *subcommand],
                cwd=folder, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=900, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise NoGo("Private scanner unavailable or timed out") from exc
        if result.returncode != 0:
            raise NoGo("Private scanner did not PASS (findings or execution error)")
    return {
        "source": "PRIVATE local checkout",
        "gitleaks_all_refs": "PASS",
        "gitleaks_worktree": "PASS",
        "refs_inspected": len(refs),
        "reachable_commits": count,
        "private_pr_issue_actions_audit": "NOT RUN",
        "historical_author_metadata_review": "NOT VERIFIED",
        "pii_review": "NOT VERIFIED",
        "licenses_and_rights": "NOT VERIFIED",
        "transitive_dependency_sbom": "NOT RUN",
        "private_backup_restore": "NOT RUN",
        "public_export_authorized": False,
        "android_build": "NOT RUN",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--private-checkout", type=Path, required=True)
    args = p.parse_args()
    try:
        result = scan(args.private_checkout)
    except (NoGo, FileNotFoundError) as exc:
        raise SystemExit("NO-GO: " + str(exc)) from exc
    print(json.dumps(result, indent=2))
    print("NO-GO: automated secret scans are not publication/legal approval.")


if __name__ == "__main__":
    main()
