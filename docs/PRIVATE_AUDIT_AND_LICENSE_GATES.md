# Private-source security and rights gates — NOT APPROVED

This public document contains **procedures only**. It must not include real private source files, credentials, personal data, scan logs, or proprietary reports.

## A. Private checkout — reproducible restricted preflight

In an isolated, trusted working environment with an authorized **complete local clone** of `ftmstr/E-Clock`, and only on branch `ci/zero-history-public-build-prep-20261017`:

```bash
python3 tools/private_audit_preflight.py --private-checkout /path/to/trusted/private/E-Clock
```

The tool is **public** and may be copied to the trusted environment; the Private repository is never copied to Public. The script rejects a shallow clone, dirty checkout, wrong remote, wrong branch and missing scanner. It runs `gitleaks git --log-opts=--all` and `gitleaks dir` with redacted/suppressed outputs. A tool failure or finding blocks progress; it does **not** claim that code is clean when a scanner fails. Scan findings require confidential investigation, secret revocation/rotation and an updated scan before any publishing decision. Scanner PASS is only a narrow automated check. The official Gitleaks documentation describes `git`, `dir` and `--log-opts`: https://github.com/gitleaks/gitleaks

**Today these two scans have NOT RUN against the actual Private source**; only synthetic tests were executed on Public CI. Do not mark a release approved based on the public simulation.

## B. Completeness gaps — require separate evidence

| Review gate | Current status | Private evidence required |
|---|---|---|
| Reachable historical Git secrets | NOT RUN | Complete Gitleaks all-refs output and remediation evidence |
| Entire selected source snapshot | NOT RUN | Strict tree/dir scan, hashed clean export and inspection |
| Authors, PR and issue personal information | NOT VERIFIED | Commit/PR/issue/export metadata audit without disclosure |
| GitHub Actions logs and old artifacts | NOT VERIFIED | Run/job/asset inventory and leak review |
| PII in test fixtures, identifiers and documents | NOT VERIFIED | Manual + automated privacy review |
| Private backup integrity and restoration | NOT VERIFIED | Offline checksummed backup and successful restore |
| Source copyright ownership and third-party reuse | NOT VERIFIED | Owner assertion and actual source provenance |
| Direct and transitive Maven/Gradle licenses | NOT RUN | Resolved graph/POM/SPDX/SBOM and required attribution |
| Android APK embedded licenses/notices | NOT RUN | Release/debug artifact dependency and notice audit |
| Google Play Services and Wear OS conditions | NOT VERIFIED | Official distribution/licensing policy review |
| Logo/font/alarm sound legal rights | BLOCKED | Origin/license files, permitted media use and metadata audit |
| Public branch protection and rulesets | NOT VERIFIED | Admin UI/API readback; connector got 403 |
| Admin-managed SHA-256 seal and evidence | NOT APPROVED | Source + audit hash and independent actual approval |
| Android tests, lint, APK and on-device timing | NOT RUN | Actual Gradle and physical/emulator runs |

The Private selected branch HEAD has 309 Git blobs (not a complete historical security audit). HEAD filename inventory did not reveal obvious packaged media, signing keys or LICENSE/NOTICE entries. **Absence of a file at HEAD is not a license conclusion.**

## C. Gradle dependency-license queue

Real Private build catalog: AGP 9.4.0, Kotlin 2.2.10, KSP 2.3.12, Room 2.8.5, Coroutines 1.10.2, Compose BOM 2026.09.00, Wear Compose 1.6.2, Google Play Services Wearable 20.0.1, DataStore 1.2.1; the app modules include AndroidX and JUnit. These are **source manifest versions, not a resolved dependency graph**.

- Android Gradle plugin and Kotlin compiler/Compose compiler: inspect POM/LICENSE for the exact resolved binaries; build-time vs distributed dependencies must be distinguished.
- AndroidX Room, Compose, Material3, DataStore, Activity, Core and Wear Compose: inspect exact Maven POM dependencies, transitives, licenses and packaging notices.
- Google Play Services Wearable Data Layer: verify redistribution terms, Play Services device requirements and matched phone/watch app identity/signature; do not assume the library is under the same terms as AndroidX.
- Coroutines and JUnit: verify actual resolved versions and notices where applicable.
- Examine proprietary or user-provided assets **outside Public**; do not publish unidentified images/audio.

All above are **PENDING**, not PASSED. A license selection, legal ownership decision or NOTICE file must not be fabricated by CI.

## D. Export compatibility

The original Private `scripts/prepare-public-snapshot.py` assumes a fresh one-commit Git repository and includes a legacy malformed workflow. It must never be imported verbatim into the Public bootstrap. Our Public handoff uses the **known Public root commit** and a two-part independently approved seal.

Do not run an automatic public push. Once all approvals exist, stage only reviewed allowlisted source in a fresh **local** directory, verify the final manifest, review the effective public diff and only then consider a normal Public PR. No private branches, tags, commit ancestry, credentials, device data or private reports may be transferred.

## E. Final state for this tour

Public security synthetic CI can PASS while real private audit remains NOT RUN and Android CI intentionally stays NO-GO. This separation is intentional and must be preserved.
