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
