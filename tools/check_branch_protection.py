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
REQUIRED_JOB = "Synthetic public audit contract tests"


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
    protection = branch.get("protection")
    status = protection.get("required_status_checks") if isinstance(protection, dict) else None
    if not isinstance(status, dict) or status.get("enforcement_level") not in ("non_admins", "everyone"):
        raise PolicyBlocked("Required Public CI check policy NOT ENFORCED")
    contexts = status.get("contexts", [])
    checks = status.get("checks", [])
    if not isinstance(contexts, list) or not isinstance(checks, list):
        raise PolicyBlocked("Required Public CI check policy malformed")
    actual = {x for x in contexts if isinstance(x, str)}
    actual.update(x.get("context") for x in checks
                  if isinstance(x, dict) and isinstance(x.get("context"), str))
    if REQUIRED_JOB not in actual:
        raise PolicyBlocked("Synthetic Public CI job is NOT REQUIRED")
    return {"repository": EXPECTED, "branch": BRANCH, "protected": True,
            "required_ci_check": REQUIRED_JOB,
            "rule_details": "PR reviews, bypass, force-push and deletion NOT VERIFIED; independent admin review required"}


def main():
    try:
        result = check(os.environ.get("GITHUB_REPOSITORY", ""),
                       token=os.environ.get("GITHUB_TOKEN", ""))
    except PolicyBlocked as exc:
        raise SystemExit("NO-GO: " + str(exc)) from exc
    print(f"Protected main and required synthetic CI status PASS for {result['repository']}:{result['branch']}. "
          "Pull-request review, bypass actors, force-push/deletion and rulesets remain NOT VERIFIED.")


if __name__ == "__main__":
    main()
