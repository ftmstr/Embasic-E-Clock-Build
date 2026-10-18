#!/usr/bin/env python3
"""Review EVERY reachable PUBLIC Git tree/blob, including files later deleted.

Fail-closed conservative hygiene, not a substitute for Gitleaks, privacy, or IP
rights review. Designed to run on the intentionally-public bootstrap only.
"""
from __future__ import annotations
import re
import subprocess
from pathlib import Path
from verify_snapshot import PUBLIC_ROOT, safe_path, Blocked

MAX_BLOB = 5 * 1024 * 1024
ASSETS = {".png", ".webp", ".jpg", ".jpeg", ".svg", ".ttf", ".otf"}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----"),
    re.compile(rb"(?:ghp_|gho_|ghs_|github_pat_)[A-Za-z0-9_]{16,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
    re.compile(rb"(?i)C:\\Users\\[^\\\s]+"),
)


def git(root: Path, *args: str, stdin: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=root, input=stdin, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, check=True, timeout=60,
    ).stdout


def inspect(root: Path, trusted_root: str = PUBLIC_ROOT) -> dict[str, int]:
    root = root.resolve()
    try:
        if git(root, "rev-parse", "--is-shallow-repository").strip() != b"false":
            raise Blocked("Shallow public history")
        roots = git(root, "rev-list", "--all", "--max-parents=0").decode().splitlines()
        if roots != [trusted_root]:
            raise Blocked("Public Git history contains an unexpected root")
        commits = git(root, "rev-list", "--all").decode().splitlines()
        if not commits:
            raise Blocked("Empty public history")
        seen: set[str] = set()
        count = 0
        for commit in commits:
            for entry in git(root, "ls-tree", "-r", "-z", commit).split(b"\0"):
                if not entry:
                    continue
                meta, tab, name = entry.partition(b"\t")
                if not tab:
                    raise Blocked("Malformed historical Git entry")
                mode, kind, blob = meta.split()
                path = name.decode("utf-8", "strict")
                if mode not in (b"100644", b"100755") or kind != b"blob" or not safe_path(path):
                    raise Blocked("Forbidden historical path, mode or Git link")
                blob_hash = blob.decode("ascii")
                if blob_hash in seen:
                    continue
                seen.add(blob_hash)
                size = int(git(root, "cat-file", "-s", blob_hash).strip())
                if size > MAX_BLOB:
                    raise Blocked("Oversized historical source or asset")
                data = git(root, "cat-file", "blob", blob_hash)
                if any(pattern.search(data) for pattern in SECRET_PATTERNS):
                    raise Blocked("Potential historical credential; private investigation required")
                if Path(path).suffix.lower() not in ASSETS:
                    if b"\0" in data:
                        raise Blocked("Historical text file contains binary NUL")
                    data.decode("utf-8", "strict")
                count += 1
            # Commit messages are public and must not include even old credentials.
            message = git(root, "log", "-1", "--format=%B", commit)
            if any(pattern.search(message) for pattern in SECRET_PATTERNS):
                raise Blocked("Potential credential in public commit message")
        return {"commits": len(commits), "unique_blobs": count}
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, UnicodeError,
            ValueError, OSError) as exc:
        raise Blocked("Unable to inspect entire reachable public history") from exc


def main() -> None:
    try:
        result = inspect(Path.cwd())
    except Blocked as exc:
        raise SystemExit("NO-GO: " + str(exc)) from exc
    print(f"Public history hygiene PASS: {result['commits']} commits, {result['unique_blobs']} distinct blobs. This does NOT mean Private Gitleaks PASS.")


if __name__ == "__main__":
    main()
