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


## Tur 4: Public Git history scanner (actually run in Public CI)

`tools/audit_public_git_history.py` traverses **all reachable Public commit trees**, not just the current index; checks historical filenames and file modes, scans old textual Git blobs and commit messages for selected high-confidence credential signatures, and rejects previously-added-and-deleted forbidden files and symlinks. The scan runs with checkout `fetch-depth: 0`, before the source/audit release gate. It is an extra conservative hygiene layer **not a complete Gitleaks, DLP/PII, or legal review**. It does not scan Private Git history and does not validate binary metadata / archive internals.

## Tur 4: Draft transitive dependency queue — from PRIVATE local Gradle only

A second, public-source-only script `tools/gradle_dependency_preflight.py` may be carried to a trusted environment. It has no network publication or Git push operations. It requires a clean, full, authorized Private clone on the dedicated preparation branch, a verified Gradle 9.6.0 executable and **pre-populated local dependency caches**, and runs the six modules' `debugRuntimeClasspath` dependency graph tasks with `--offline`. A failed resolution, missing Gradle, wrong remote or dirty checkout blocks execution. Its output is a **new private file outside the checkout**, chmod 0600, containing only *draft coordinates and NOT VERIFIED license statuses*:

```bash
python3 tools/gradle_dependency_preflight.py \
  --private-checkout /trusted/private/E-Clock \
  --gradle /trusted/gradle-9.6.0/bin/gradle \
  --private-report /trusted/restricted/eclock-resolved-draft.json
```

The Kotlin Gradle version catalog in Private defines direct aliases for AndroidX Compose, Room, DataStore, Wear Compose, Play Services Wearable, Coroutines, JUnit, AndroidX Test, and compiler plugins. A version catalog is **not** the actual resolution graph. The queue script parses Gradle text output and therefore cannot guarantee all artifacts/variants, classifiers, BOM constraints, parent POM inheritance, distribution metadata, embedded native binaries or build-time plugin dependencies. It is explicitly a draft only; no actual Private Gradle invocation took place in Public CI.

Before license approval, run online locked/resolved per-variant reports under controlled permissions, compare with the offline draft, collect corresponding Maven POM `<licenses>`, parent POMs, `.module` metadata, SPDX identifiers, notices and bundled Android assets. Confirm obligations for both phone and Wear APK and all transitive components. Google documents that its OSS licenses tooling can derive notices from POMs but this does **not** replace legal ownership decisions: https://developers.google.com/android/guides/opensource . Maven's POM license element is described at https://maven.apache.org/pom.html . Gradle resolution is variant-aware: https://docs.gradle.org/current/userguide/graph_resolution.html .

The build's Android Gradle Plugin 9.4.0 compatibility baseline is Gradle 9.6.0, JDK 17, Build Tools 36.0.0, compileSdk 37 according to https://developer.android.com/build/releases/agp-9-4-0-release-notes . Actual private build NOT RUN.

## Branch and approval management

Public `main` branch-protection readback returned HTTP 403 `Resource not accessible by integration`. Do not infer that branch protection is enabled or disabled; the administrator must inspect Settings → Rules → Rulesets / Branch protection and ensure reviews, no force-push/deletion, required checks and limited bypasses. The administrator-managed Actions approval seal cannot be verified via the connected read-only endpoint, and remains **NOT VERIFIED/NOT APPROVED**. A repository variable by itself is not a substitute for genuine restricted administrative permissions or independent code review.


## Tur 5: Actual GitHub branch policy failure and PR-safe CI

On 19 October 2026, a **read-only GitHub API** query to `GET /repos/ftmstr/Embasic-E-Clock-Build/branches/main` returned `protected: false`; the repository rulesets list returned empty. This is a **confirmed NO-GO**, not merely an authorization error to the detailed protection endpoint. The detailed `branches/main/protection` endpoint remains unavailable (403).

The public `tools/check_branch_protection.py` now performs a fresh read-only GitHub branch readback on the protected `main` expectation and blocks source approval when it is unprotected, unavailable, malformed or for the wrong repository. This is executed before the source manifest check. A `protected: true` response is **necessary, not sufficient**: only an administrator can additionally verify exact required checks, PR reviews, force-push/deletion bans and bypass permissions.

Administrator action in GitHub: **Embasic-E-Clock-Build → Settings → Branches → Add branch protection rule** (or **Settings → Rules → Rulesets**), target `main`, require PR reviews and the **Synthetic public audit contract tests** check, disallow force pushes and deletions, and limit bypasses. Never select the overall deliberately red Android workflow as a permanent required check while the source audit is intentionally NO-GO. After source rights review and branch-rule verification, revisit which status checks are mandatory. GitHub Free supports branch protections for public repositories.

To avoid deadlocking reviews, `.github/workflows/android-ci.yml` now also triggers on `pull_request` targeting `main`, with read-only token permissions and **synthetic checks only**; source audit and phone/Wear build remain restricted to `main`. No source merge or PR was performed to test a real PR event. Static synthetic workflow-contract tests verify this design; **actual PR-event execution NOT RUN**.

GitHub official: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches .

## Tur 5: Restricted Private HEAD content spot check — NOT Gitleaks

A read-only GitHub connector accessed only **12 selected Private HEAD text files**: root Gradle files and version catalog, two application manifests, three GitHub workflow YAMLs and three Private snapshot/test scripts. Simple high-confidence credential-prefix and assignment patterns returned no matches in this selection; no raw content, credentials or identifying values were exported. This is **not** a complete source file scan, does not enumerate all 309 HEAD blobs or historical commits, and **does not count as Gitleaks PASS**. There is no authorized full Private Git clone or Gitleaks executable in the accessible execution environment; real Private full-history Gitleaks remains NOT RUN.

## Tur 5: Offline POM declaration evidence — license verdict is NOT VERIFIED

`tools/pom_license_preflight.py` consumes the output of the **Private-only** Gradle dependency draft and local Maven POM files laid out as `group/path/artifact/version/artifact-version.pom`. It records SHA-256 of actual POM bytes, declared license name/URL, parent POM coordinates and missing metadata, all in a **new, restricted Private output file**. It rejects unsafe DTD/entity XML, missing/invalid input, malformed coordinates and unapproved drafts. Maven POM license tags represent **publisher declarations only**, not legal permission. Inherited parent licenses, SPDX normalization, actual delivered APK notices and transitive redistribution conditions remain NOT VERIFIED. It never uploads source, Maven metadata, assets or reports to Public.

Example in the trusted PRIVATE processing environment (never in this Public repository):

```bash
python3 tools/pom_license_preflight.py \
  --private-draft /restricted/eclock-deps-draft.json \
  --pom-root /restricted/maven-pom-cache \
  --private-report /restricted/eclock-pom-evidence.json
```

The direct version catalog readback is **not a resolved Gradle dependency tree**. Maven POM endpoint retrieval in the current execution environment did not succeed, and no actual Private Gradle resolution was performed. Published third-party indexing indicates one Room 2.8.5 artifact declares Apache-2.0, but this observation does **not** establish all dependency licenses or obligations. License compliance remains blocked until complete runtime/build-time resolved graph, POM parent inheritance, notices and legal source provenance are reviewed.

For dependency checksum provenance see https://docs.gradle.org/current/userguide/dependency_verification.html — auto-generated checksums need human verification and cannot substitute for a license review.
