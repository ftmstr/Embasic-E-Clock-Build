#!/usr/bin/env python3
"""Fail-closed read-only GitHub branch protection precondition for Public CI.

A protected branch is necessary but NOT sufficient for an approved policy.
Human verification of required checks and force-push/deletion restrictions
is still mandatory. This script never changes repository settings.
"""
from __future__ import annotations
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EXPECTED = "ftmstr/Embasic-E-Clock-Build"
BRANCH = "main"


class PolicyBlocked(Exception):
    pass


def check(repo: str = EXPECTED, opener=urlopen, token: str = "") -> dict[str, object]:
    if repo != EXPECTED or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise PolicyBlocked("Unexpected repository; refusing a different approval target")
    url = f"https://api.github.com/repos/{EXPECTED}/branches/{BRANCH}"
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "embasic-eclock-public-branch-gate"}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with opener(Request(url, headers=headers), timeout=15) as response:
            if response.status != 200:
                raise PolicyBlocked("GitHub branch-policy readback failed")
            payload = response.read(1024 * 1024 + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise PolicyBlocked("GitHub branch-policy API unreachable or inaccessible") from exc
    if len(payload) > 1024 * 1024:
        raise PolicyBlocked("GitHub policy response unexpectedly large")
    try:
        branch = json.loads(payload)
    except (ValueError, UnicodeError) as exc:
        raise PolicyBlocked("GitHub branch-policy response invalid") from exc
    if not isinstance(branch, dict) or branch.get("name") != BRANCH:
        raise PolicyBlocked("GitHub branch-policy response is not for main")
    if branch.get("protected") is not True:
        raise PolicyBlocked("Public main branch is NOT PROTECTED")
    return {"repository": EXPECTED, "branch": BRANCH, "protected": True,
            "rule_details": "NOT VERIFIED; administrator review still required"}


def main():
    try:
        result = check(os.environ.get("GITHUB_REPOSITORY", ""),
                       token=os.environ.get("GITHUB_TOKEN", ""))
    except PolicyBlocked as exc:
        raise SystemExit("NO-GO: " + str(exc)) from exc
    print(f"Branch protection boolean PASS for {result['repository']}:{result['branch']}. "
          "Required checks, bypass actors and ruleset details require independent admin review.")


if __name__ == "__main__":
    main()
