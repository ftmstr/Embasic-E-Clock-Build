# Public snapshot handoff contract — NO-GO until independent review

This is a **public-only procedure**, not permission to export Private E-Clock code. The Private repository, its PRs, history, actions artifacts, reports, media and signing credentials are never to be copied to this repository.

## Verified bootstrap

- Official Public destination: `ftmstr/Embasic-E-Clock-Build`.
- Root commit: `9ba88a5482e30ddb3834e79dede8240af13185c3`.
- Its subsequent infrastructure commits are legitimate; checking that history contains *exactly one commit* is incompatible with this repository. Instead, `tools/verify_snapshot.py` requires exactly this trusted root, full history, no additional branch/tag, known file modes and a precise reviewed manifest.
- Never merge, mirror, rebase, cherry-pick or force-push any Private ancestry here. Do not replace the Public Git root.

## Private-to-Public staging — only after private audit

1. In an isolated trusted **Private** checkout, verify the intended source revision, clean worktree, previous sensitive metadata, all accessible code/history/issue/action logs and source ownership. Run real Gitleaks and privacy scanning. The existing Private `scripts/prepare-public-snapshot.py` outputs a *draft only*; `--strict` is necessary but not sufficient.
2. The legacy exporter includes `.github/workflows/public-snapshot-android.yml`, which has a malformed/duplicated shell block, requires a one-commit target, and must **not** be imported. Use the Public `.github/workflows/android-ci.yml` instead. The Private exporter's old `inventory_sha256` and `files` accounting must be recalculated against the *actual sanitized Public working tree*, not copied as proof.
3. Copy only inspected, explicitly approved code files from `app-phone/`, `app-wear/`, `core/model/`, `core/alarm/`, `core/data/`, `core/sync/`, the four approved root Gradle paths and necessary Android manifests. Source/ABI contracts remain unchanged. Do not carry source commit metadata, tags, branch history, `docs/` from Private, assets without known redistribution rights, APK, ZIP, JAR, keystore, logs, user/device data or media from Drive.
4. Independently verify Maven/Gradle direct and transitive dependencies, source and APK redistribution notices, font/logo/audio rights, and Play Services/Wear OS terms. No `LICENSE` or legal approval is to be fabricated. Repeat secret scan on **final effective Public candidate**.
5. Before publication, record a Private audit with evidence IDs and precise source + asset digests in the Private Google Drive project folder. Do not place private report content, reviewer identities, email addresses or private scanner logs in Public.
6. After authorized clean source files are committed to Public through **new Public commits only**, compute the following draft manifest from their exact tracked bytes. `source_files` is the lexically sorted list of tracked files excluding `INFRA_FILES` and `SNAPSHOT-AUDIT.json`; `source_inventory_sha256` is SHA256 of a trailing-newline-terminated sorted list of `<file SHA256>  <path>` for source files. `public_inventory_sha256` uses the same algorithm on *all tracked files except `SNAPSHOT-AUDIT.json`*, including public workflows, tests and README. The audit file itself is excluded to prevent self-referential hashing. Fill `reviewed_asset_sha256` with an exact path-to-SHA mapping; an empty mapping is valid only when there are zero assets.
7. Treat `SNAPSHOT-AUDIT.json` claims as **assertions, not proof**. Set its fields to `PASS/VERIFIED/APPROVED` only after actual audit and authorized legal/human approval. The repository administrator must **separately** set the repository **Actions variable** `ECLOCK_APPROVED_PUBLIC_SHA256` equal to the **approval seal** calculated as SHA256 of `public_inventory_sha256 + newline + SHA256(SNAPSHOT-AUDIT.json exact bytes) + newline` *after* independent inspection. This also seals the claimed audit/rights statuses against later alteration. This variable is intentionally unset today. Reset it whenever any public file or the audit claims change, even a workflow edit.
8. With repo branch protection, administrator review and repository-variable access restrictions enforced independently, GitHub Actions can then attempt the core/phone/wear debug build. A green build does not demonstrate device timing, paired signatures, STOP/SNOOZE transport, Doze, Direct Boot or DST reliability.

## Required manifest format — illustration ONLY, not an approved record

```json
{
  "automated_secret_scan": "NOT RUN",
  "private_history_audit": "NOT VERIFIED",
  "source_rights_approved": "NOT APPROVED",
  "artifact_redistribution_approved": "NOT APPROVED",
  "public_approval": "NOT APPROVED",
  "source_files": [],
  "source_inventory_sha256": "",
  "public_inventory_sha256": "",
  "reviewed_asset_sha256": {}
}
```

Do **not** commit this illustrative JSON as an approval and do not set the Actions variable without independent evidence.

## Administrator-controlled seal derivation (only after actual approval)

From the exact audited Public working tree, compute the seal locally:

```python
import hashlib
from pathlib import Path
audit_hash = hashlib.sha256(Path("SNAPSHOT-AUDIT.json").read_bytes()).hexdigest()
tree_hash = "<reviewed public_inventory_sha256 from audited file>"
seal = hashlib.sha256((tree_hash + "\n" + audit_hash + "\n").encode()).hexdigest()
print(seal)
```

The repository variable `ECLOCK_APPROVED_PUBLIC_SHA256` is the seal, **not** the raw tree digest. Do not set it based solely on repository claims. The approver must inspect the private evidence before setting it, and must enforce branch protection separately.

## Validation commands

```bash
python3 -m unittest discover -s tools -p 'test_*.py' -v
ECLOCK_APPROVED_PUBLIC_SHA256= python3 tools/verify_snapshot.py
```

The second command must exit nonzero while source audit evidence is missing.

## Operational limitations

- A regex/path scan and file hash are not a complete secret audit or IP review.
- Branch history rooting and admin-managed variable approval require actual GitHub branch protection, secret hygiene and independent human review; in-repository checks alone cannot replace repository permissions.
- CI emits no APK artifacts before the source-audit job succeeds.
- Separate GitHub-hosted debug builds may be signed with different ephemeral debug certificates. They are **not** a validated phone/watch Data Layer pair. Paired device tests must use matching developer-controlled **non-production** test signing in a trusted environment.


## Tur 5: Mandatory live GitHub branch-policy gate

On 19 October 2026, GitHub REST `GET /repos/ftmstr/Embasic-E-Clock-Build/branches/main` returned **`protected: false`**. The active rulesets list was empty. Detailed branch-protection settings returned 403 to the connected integration. The source-release gate now calls `tools/check_branch_protection.py` before the snapshot verifier and rejects `protected != true` or API errors. **This repo is NO-GO for source publication until the administrator protects `main` and separately verifies the exact enforcement policy.**

Set the rule in GitHub Settings → Branches or Rules → Rulesets. Require a pull request with review, disallow deletion/force-push and constrain bypass actors. The read-only **Synthetic public audit contract tests** job is designed to run on PRs. The source-audit/Android jobs do not run on PRs; they remain reserved for reviewed code on `main`. A genuine PR CI run has **NOT RUN** yet. Do not require the intentionally failing source-audit job as an immediate merge prerequisite before an approved snapshot exists. Revisit required checks once release approval is possible.

The temporary presence of an ordinary feature branch may be rejected by the strict single-public-branch source-audit check; clean up completed review branches before any release. Never delete or rewrite the trusted Public root to resolve this.

## Restricted POM evidence queue

Use `tools/gradle_dependency_preflight.py` only in a complete Private checkout to obtain a **draft resolved graph**. Separately, `tools/pom_license_preflight.py` accepts this Private JSON and **locally curated offline Maven POMs** to collect exact POM hashes and raw publisher license declarations. It neither downloads Private source nor approves licences. Missing/parent-inherited POM rights, SPDX alignment, third-party media, NOTICE requirements and phone/Wear redistributable bundles require explicit offline review; no actual resolved Private dependency graph has yet been produced.

Before publication, review complete private Gitleaks + PII + source-rights evidence; run secret scans on the actual sanitized candidate and complete independent admin source/Audit seal. These actions remain **NOT RUN / NO-GO**, respectively.


## Tur 6 — Metadata-only legacy exporter compatibility checker

The Private legacy script's actual output has **additional inherent incompatibility**: `ROOT_FILES` requires `.github/workflows/public-snapshot-android.yml`, but `ALLOWED_SUFFIXES` does not include `.yml`. The script's own `check_name()` rejects that mandatory workflow. It also embeds invalid/duplicated shell logic. **Do not fix this by adding `.yml` to the Public source allowlist or copying the unsafe workflow.**

The Private preparation-branch HEAD has 309 tracked blobs; the legacy file selection algorithm would choose 276 files, including the one forbidden workflow. This was verified from the authenticated GitHub tree *names and sizes* only. This is not a completed export or rights review.

Use `tools/legacy_export_compatibility.py --local-legacy-export /trusted/private/staging` in a restricted processing environment **only on an already created review directory**. It inspects its filenames and legacy JSON audit, prints non-sensitive status codes, **does not open source-file bytes**, and exits with code 2 even when the provided claims appear approved. It will not copy or push any files. The 9 regression tests are synthetic.

A future safe process must independently select and review Private source files, omit old workflow and Private READMEs/history, produce the new exact source/public SHA inventories and asset-rights evidence, verify Gitleaks + PII + transitive licences, obtain real independent review and branch protection, and set the external administrator approval seal *only then*. No such source transfer has been authorized.
