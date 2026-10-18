# Embasic E-Clock — Public Build Infrastructure

This separate public repository is reserved for **security-reviewed, zero-private-history Android and Wear OS CI**. It is not the private development repository. Do not mirror, merge, or push private Git history, secrets, user data, signing keys or unapproved third-party assets here.

**STATUS: NO-GO — Kotlin source publication and APK builds blocked pending private Gitleaks/PII/license/source audit.**

Architecture to preserve: `app-phone`, `app-wear`, `core:model`, `core:alarm`, `core:data`, `core:sync`; Kotlin, Jetpack Compose, Compose for Wear OS, Gradle Kotlin DSL, Room, DataStore, Coroutines/Flow, Wearable Data Layer, AlarmManager and local-first alarms.

Build verification must independently run Android phone, Wear OS, shared-core unit tests and lint on an Ubuntu GitHub-hosted runner after source audit. Real-device tests remain separate. No production signing or fake PASS statuses.

GitHub Actions is intentionally fail-closed until a source snapshot is fully audited and approved. The repository's initial commit is a clean public-only bootstrap; future public commits must not import private commit ancestry.

## Security-first development status (Tur 3)

- `tools/verify_snapshot.py`: fail-closed validation of trusted Public root ancestry, allowlisted paths, source/asset SHA-256, reviewed audit JSON and independent administrator-managed approval seal.
- `tools/private_audit_preflight.py`: local-only Gitleaks full-ref and working-tree scans for a complete **Private** checkout. It does not export files or grant publication approval.
- `tools/test_verify_snapshot.py` and `tools/test_private_audit_preflight.py`: isolated synthetic regression suite; no production code, signatures or personal information in these fixtures.
- [Private audit and license gates](docs/PRIVATE_AUDIT_AND_LICENSE_GATES.md) and [public snapshot handoff](docs/PUBLIC_SNAPSHOT_HANDOFF.md) list the remaining security/legal approvals.

A green **synthetic** CI job is not a phone/Wear Gradle or device reliability result. Real Gitleaks on the Private repository, privacy/history/asset review, transitive dependency licenses, actual builds and physical-device tests remain **NOT RUN / BLOCKED**. CI deliberately refuses unapproved source builds.
