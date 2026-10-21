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


## Tur 6 — 20 October 2026: source-export handoff findings, no publication

- Public bootstrap baseline remained `c5dc8eb94117e5615fff5f0194d55c584e709e89` before Tur 6.
- The actual Private exporter's `ROOT_FILES` requires `.github/workflows/public-snapshot-android.yml` while `ALLOWED_SUFFIXES` **omits `.yml`**. Its `check_name()` therefore rejects one of its own mandatory files; the legacy workflow also contains duplicated/malformed shell content and should never be imported.
- Its audit JSON uses `files`, `inventory_sha256`, `zero_git_history`, `private_issue_pr_actions_history_review`, and `public_approval=HUMAN REVIEW REQUIRED`. This is incompatible with the existing reviewed Public root and its `source_files`, `source_inventory_sha256`, `public_inventory_sha256`, asset-rights map, complete private-history review, and separately set approval seal. The legacy exporter **must not** be patched into unconditional publication.
- Filename-based inspection of the Private preparation-branch HEAD (GitHub tree truncated=false) gives **309 blobs, 276 paths selected by the legacy exporter's rules, including the malformed workflow**. There are 275 other candidate paths and 33 excluded. No file-byte secret scan or legal-rights determination is implied. No selected PNG/JPEG/WebP/SVG/font assets were present at that HEAD.
- A further *read-only, bounded* private-content check fetched 15 large Kotlin HEAD blobs (~465 kB) via the authenticated connector and checked a handful of credential signatures. No matches for those specific patterns. This is **NOT Gitleaks, NOT 309-file coverage, and NOT historical Git scan**; no private source was printed or committed to Public.
- `tools/legacy_export_compatibility.py` is an **offline metadata-only NO-GO analyzer**. It never copies source, authorizes publication or uploads a snapshot. It checks the legacy manifest schema, prohibited workflow, mandatory source paths and missing security/rights evidence, and exits nonzero by design. Its tests use synthetic fixtures only.
- Verified baseline GitHub Issues: `#2` is still **OPEN**. `GET /repos/ftmstr/Embasic-E-Clock-Build/branches/main` currently returns `protected:false`; `GET /rulesets` is empty. A configured branch rule is a precondition but not sufficient legal/secret/publication approval.
- Current environment: no `gitleaks`, no `gradle`, no authenticated full Private Git clone. A read-only direct `git ls-remote` fails DNS. **True Private Gitleaks `git --all` and `dir`, actual resolved Gradle/POM SBOM and APK rights remain NOT RUN**.
- Official release corroboration: Android's Room 2.8.5 release notes show 9 September 2026; Google Play Services setup lists `play-services-wearable:20.0.1`. Secondary artifact indexing advertises Apache-2.0 for individual Room runtime components, but **does not prove complete resolved direct/transitive license compliance** or provide source ownership and redistribution approval.

No change in approval policy: **Private repositories stay private; no source snapshot, test signing material, logo/audio, PII, APK or private Git history may be published until real scans and independent rights sign-off.**


## Tur 7 — 20 October 2026: POM identity and reviewed notices (synthetic scope)

Public readback remained the source-free root `0c15f08088b0f2ed0f836794e8e3edaefe286a52` on arrival. Actions #39348669288 proved 63/63 synthetic tests and a PASS on 44 Public Git revisions, while source approval stayed NO-GO with branch `protected:false`. Issue #2 remains open, no effective rulesets. Private `ftmstr/E-Clock` is still PRIVATE.

**New real security logic:** `tools/pom_license_preflight.py` now checks a POM's effective `groupId:artifactId:version` (allowing group/version inheritance from a declared Maven parent) against the resolved component being evaluated; a mismatched, incomplete or unresolved identity fails closed. Previously an incorrectly located or substituted POM could contribute irrelevant license metadata. Symlinked POMs are rejected before a missing-file fallback. Synthetic regression tests include conflicting artifact and version, and linked POM metadata. These changes are **not** a real resolved Gradle/POM license scan; parent license inheritance, POM authentication, SPDX normalization and legal redistribution still require human review.

**Rights and notice contract:** `tools/verify_snapshot.py` now optionally accepts `LICENSE`, `NOTICE`, and `THIRD_PARTY_NOTICES.md` as reviewed, hash-sealed source-side files. They are not required where rights have not been established, are not created in this tour, and do **not** create any license grant. The independent administrator-approved inventory must cover their exact bytes before any build is allowed. Never synthesize third-party attribution or claim a missing LICENSE establishes permission to redistribute.

Maven POM official reference: https://maven.apache.org/pom.html — `groupId`, `version`, and `licenses` can be inherited from a parent POM; a license declaration does not on its own prove redistribution rights.

**True private scans still NOT RUN:** complete Private Gitleaks on all reachable refs and working files, entire 309-blob HEAD PII inspection, historic issues/PR/Actions/logs, online resolved Gradle graph, actual POM ancestry/NOTICE review. No Android core/phone/wear build, APK or physical paired-device verification. Source export is NO-GO and no Private source bytes/history or proprietary assets were written to this Public repository.

### Tur 7 weighted audit readiness snapshot (indicative, not product-completion %)

| Gate | Weight | Confirmed readiness | Weighted points |
|---|---:|---:|---:|
| Isolated Public bootstrap/root/historical guard | 15 | 100% | 15 |
| Public synthetic tests and safe CI routing | 10 | 100% | 10 |
| Actual complete Private Gitleaks and PII | 20 | 0% | 0 |
| Effective admin branch protections | 10 | 0% | 0 |
| Actual resolved dependency and license evidence | 15 | 0% | 0 |
| Review-only snapshot handoff tooling | 15 | 30% (heuristic) | 4.5 |
| Real Android builds and device testing | 10 | 0% | 0 |
| Evidence chain and private Drive reporting | 5 | 100% | 5 |
| **TOTAL** | **100** | **34.5% estimated** | **34.5** |

This weighted score is a transparent **process-readiness estimate**, not a measured fraction of shipped phone/Wear functionality. The 30% handoff line means the compatibility and manifest tools exist, not that publication has occurred. A green synthetic test count does not increase the unrun Gitleaks/build/license gates.


## Tur 8 — 20 October 2026: Private Git object completeness guard (NOT A PRIVATE SCAN)

Live Public baseline: `9d27834bd5292c8a6d96e2a8ddde3d81efdf18ff`, Actions #39349746239 — **67/67 synthetic PASS**, Public history 49 commits/49 unique blobs PASS, source audit NO-GO because Public main `protected:false`, Android builds SKIPPED, APK artifact 0. GitHub Issue #2 remains OPEN.

### Added security control

`tools/private_audit_preflight.py` now runs `git fsck --full --no-reflogs --unreachable --no-progress` **only against an already authorized full, clean, local PRIVATE clone**. It captures this output privately and suppresses it in logs; a nonzero result or ANY unreachable/dangling object fails closed **before** the two Gitleaks scans. This closes a gap: `gitleaks git --log-opts=--all` checks reachable refs, whereas old deleted commits or unreferenced blobs can still reside in a local object database. Treat any dangling objects as a manual review problem; do not auto-delete, rewrite Private history or `git gc` merely to obtain PASS.

Official Git explanation: https://git-scm.com/docs/git-fsck . The Gitleaks `git` and `dir` modes are described by its maintained upstream project: https://github.com/gitleaks/gitleaks .

**Evidence limits:** The new orphan-object branch did not receive a dedicated GitHub regression test: a test-file update was blocked by tooling security safeguards and was not retried. Existing synthetic tests still run. In Public CI, this Private preflight cannot access Private sources or Gitleaks; no actual Private `git fsck`, Gitleaks scan or completed Private Git history evidence is claimed. Even an empty local fsck does not prove all remote refs, PR/issue/Actions logs or offsite history have been reviewed.

### Restricted dependency metadata — concrete, narrow source context

The authenticated Private version catalog specifies `androidx.room:room-runtime:2.8.5` and `com.google.android.gms:play-services-wearable:20.0.1`. Google's AndroidX release documentation confirms Room 2.8.5; Google's current Play services setup lists Wearable 20.0.1. A third-party Maven package index declares Apache-2.0 for a Room runtime 2.8.5 component, **not** for the complete resolved dependency graph. No actual Private Gradle resolution, module metadata/POM inheritance, Maven SHA verification, licenses/NOTICE/SBOM or redistribution rights assessment was performed. Sources: https://developer.android.com/jetpack/androidx/releases/room , https://developers.google.com/android/guides/setup , https://mvnrepository.com/artifact/androidx.room/room-runtime-android/2.8.5 .

### Readiness scoring (unchanged estimate, not application completion)

The weighted Public build/security process-readiness rubric remains **34.5%**: bootstrap/history (15/15), synthetic CI (10/10), complete Private secret/PII (0/20), admin branch protection (0/10), actual resolved licenses (0/15), source handoff preparation (4.5/15, **30% qualitative**), Android builds+device tests (0/10), evidence+private reporting (5/5). The new preflight rule provides additional defense but does not justify credit for any **unrun** audit gate. A 67-test PASS is evidence for the Public tooling only, never a phone/Wear MVP completion figure.

### Required release blockers

1. Administrator protects Public `main` and verifies effective merge requirements/CI/force-push/deletion/bypasses (Issue #2).
2. Private owner executes actual complete-history + worktree Gitleaks and Git object inspection on a trustworthy local full clone, with confidential PII, issue/PR/Actions artifact and history review.
3. Resolve Gradle plugin, compile/runtime, KSP and phone/Wear variants with artifact provenance; inspect real POM parents, license attribution, notices, trademarks, source ownership and Google Mobile Services redistribution requirements.
4. Review isolated snapshot with exact hashes and independent approval seal. No Private ancestry/source, signing keys, proprietary assets or special reports in Public until documented approval.

Current result: **source transfer NO-GO, real Android phone/Wear build NOT RUN, no APK**.


## Tur 9 — 20 October 2026: Safer Private Gradle draft and clean Public build gate

**Baseline verified:** Public `7d712459fbe7c74624b44837cf50cb265a46207f`, Actions #39350736326; `67/67` synthetic PASS, Public history `51` commits and `51` unique blobs PASS. Private `ftmstr/E-Clock` remained private, Issue #2 remained OPEN, and GitHub branches/main readback returned `protected:false` with no active rulesets. Android build jobs were SKIPPED; artifacts zero.

The **Private-only** `tools/gradle_dependency_preflight.py` now requests **12** configuration reports rather than 6: both `debugRuntimeClasspath` and `debugCompileClasspath` for each of `:app-phone`, `:app-wear`, `:core:model`, `:core:alarm`, `:core:data` and `:core:sync`. It fails closed on additional offline resolution errors and writes the new PRIVATE draft JSON through exclusive file creation (`O_CREAT|O_EXCL` and where available `O_NOFOLLOW`) with restrictive mode `0600` *from creation*, not with a permissive temporary write then `chmod`.

Even 12 configurations **do not** fully cover Android build plugins, KSP code generators, annotation processors, test-only dependencies, all release/flavor variants, Maven BOM constraints, resolved APK artifacts, transitive POM parents or third-party NOTICE obligations. New draft report fields explicitly say `plugin_classpath_and_ksp=NOT RUN`, `resolved_artifact_files_and_checksums=NOT VERIFIED`, `transitive_license_compliance=NOT VERIFIED`, `public_export_authorized=false`. Official Gradle explains the `dependencies` and `dependencyInsight` tasks and selected/transitive graphs at https://docs.gradle.org/current/userguide/viewing_debugging_dependencies.html . Actual Private Gradle was NOT RUN.

**Public gate hardening:** `tools/verify_snapshot.py` now refuses a reviewed Git tree that also has **modified, staged, untracked or ignored files** in the build checkout; it checks after the reviewed SHA and audit assertions. This blocks an untracked local file from influencing Gradle behavior even when the source manifest appears valid. CI must use a clean source checkout. Two new synthetic regressions exercise untracked and ignored files, in addition to the existing byte hash, approval seal and path/mode tests. It neither sets the independent approval seal nor relaxes the NO-GO for missing Private scans.

**Private root/history:** The earlier read-only `git fsck --full --no-reflogs --unreachable` guard in `tools/private_audit_preflight.py` still exists and requires a trusted clean, full Private local clone. Neither that command nor the actual Gitleaks git/dir secret scanners were executed against Private in this turn; no source copy or Gitleaks PASS is claimed.

**Current security boundary:** No Private source may be uploaded to Public until administrator activates the main branch ruleset (Issue #2), real full-history and worktree secret/PII scans are complete, runtime/compile/build classpaths and POM/legal distribution rights are reviewed, independent source manifest SHA/rights approval is recorded and real Android builds are possible. The Public CI source-audit remains intentionally NO-GO; Android builds NOT RUN.

**Weighted readiness:** 15 points isolated Public root/history +10 points synthetic CI +0 Private full Gitleaks/PII +0 branch protection +0 actual resolved license +4.5/15 qualitative snapshot-handoff tooling +0 Android build/real device +5 verified private evidence = **34.5/100, indicative process preparation only**. This is not a phone/Wear functional completion metric and does not increase solely from additional synthetic tests.


## Tur 10 — 20 October 2026: Private origin spoofing guard and license-evidence limitations

**Live Public baseline before edits:** `a8e9fc6e898ba3ce05449133a1b4cb8a43b7d5b0`, GitHub Actions #39352528198. The CI log confirmed 71/71 synthetic-only PASS, Public reachable-history hygiene 56 commits/56 distinct blobs PASS, **source-audit NO-GO because main is not protected**, and zero Android artifacts. GitHub Issue #2 remained OPEN and no repository rulesets were installed. Private `ftmstr/E-Clock` remained PRIVATE.

**Change:** `tools/private_audit_preflight.py` checks the `origin` URL against an explicit exact list of `https://github.com/ftmstr/E-Clock[.git]`, `git@github.com:ftmstr/E-Clock[.git]`, and `ssh://git@github.com/ftmstr/E-Clock[.git]` values. The prior suffix-only comparison could accept a lookalike host with a matching repository path. One additional synthetic test rejects lookalike hostnames, wrong owners, Public repository URLs and local file URLs; no production Private code is accessed.

**Unresolved limitation:** A corresponding attempt to strengthen `tools/gradle_dependency_preflight.py` was blocked by the connector's safety controls, **so the Gradle inventory script still has a suffix-based origin check**. This remains a mandatory manual provenance gate for future Private Gradle inventory runs. Do not mark it validated, nor accept the resulting report as independently authenticated until this limitation is resolved using authorized workflows. Do not bypass security controls.

**Real Gitleaks status:** There is no authenticated full local Private Git checkout with installed Gitleaks/Gradle in this execution environment. The new Gitleaks preflight checks have only been exercised with **synthetic fixtures** in GitHub Actions. Real Private `git fsck`, `gitleaks git --log-opts=--all`, `gitleaks dir`, full-history PII, issue/PR/Actions-log DLP, and source-rights review remain **NOT RUN**.

**Third-party metadata reference only:** Sonatype Central publishes a Maven POM for the KSP 2.3.12 Gradle plugin marker `com.google.devtools.ksp:com.google.devtools.ksp.gradle.plugin:2.3.12` declaring Apache License 2.0, with a dependency on `symbol-processing-gradle-plugin:2.3.12`. This is **only publisher metadata for one plugin marker**, not the license of every plugin, transitive artifact, dependency variant or APK. Source: https://central.sonatype.com/artifact/com.google.devtools.ksp/com.google.devtools.ksp.gradle.plugin . Google confirms `play-services-wearable:20.0.1`: https://developers.google.com/android/guides/setup . No full resolved Gradle/POM license evidence or human legal sign-off was generated.

**Indicative security/build process readiness** remains **34.5/100**, using the existing eight weighted criteria (Public provenance 15/15; synthetic CI 10/10; actual Private full scans 0/20; effective branch protection 0/10; actual resolved licenses 0/15; handoff tooling qualitative 4.5/15; real Android device builds 0/10; private reports 5/5). This is **not an Android/Wear OS MVP completion percentage** and is not increased simply by one more synthetic test.

**No publication action:** No Kotlin application source, private ancestry, brand asset, signing material, APK or private report was copied to the Public repository. Source transfer still requires actual independent scan and redistribution approval, effective branch protection and a new hash-reviewed clean snapshot/administrator seal.


## Tur 11 — 21 October 2026: Private Gradle origin and constraint safeguards

**Verified baseline:** Public main `f00c898e7c38ec92c27b701ff97ff50786b43c8c` and Actions #39409946100 (72/72 synthetic PASS; 59 commits / 59 unique Public blobs hygiene PASS; source audit FAIL / NO-GO; Android matrix SKIPPED; artifacts 0). GitHub Issue #2 remained OPEN, `main` returned `protected:false` and rulesets were empty. Private E-Clock branch HEAD tree contained 309 blobs and Private repo visibility was still PRIVATE.

**Completed Public-only tooling work:** `tools/gradle_dependency_preflight.py` now reuses `trusted_private_remote` from `tools/private_audit_preflight.py`. Canonical GitHub HTTPS/SSH Private origin values are accepted; matching suffixes on lookalike hosts/other owners are rejected. This closes the Tur 10 suffix-based origin spoofing gap without ever fetching or exporting Private source. One synthetic regression explicitly covers hostile alternate hostnames. It remains essential to independently authorize the actual full Private checkout and verify it is clean/non-shallow before collection.

**Actual Gradle semantics:** Offline Gradle `dependencies` output includes `(c)` constraint-only entries, which MUST NOT be counted as resolved external artifacts; the preflight excludes them and has a synthetic regression. `(n)` means not resolvable and is now an explicit fail-closed condition. The additional dedicated `(n)` regression change was blocked by security controls and is **NOT RUN**; no special test PASS is asserted for this exact branch. Official Gradle documentation: https://docs.gradle.org/current/userguide/viewing_debugging_dependencies.html

**Boundaries:** All 12 debug compile/runtime configurations are still a DRAFT-only design. The present environment cannot run Gradle against a full authenticated Private clone, so `12/12` real graphs **NOT RUN**. Plugin/KSP/annotation-processor, test and release variant dependencies, Maven parent POM XML, SPDX/NOTICE, artifact checksums and redistribution rights remain **NOT RUN/NOT VERIFIED**. No KSP or Android artifact is cleared for redistribution merely by published Maven license declarations. Do not mark a license PASS without examining each resolved artifact and its actual conditions.

**Secret and publication barriers:** No full Private Git object database exists in this workspace to run `git fsck`, no installed authenticated Gitleaks Private scan or complete head/history/PII review occurred; private issues/PRs/Actions logs and copyright/asset rights remain outstanding. The preflight code contains fail-closed checks, not completed real Private audit evidence. The legacy private source exporter still does not match the approved Public Git root/source contract; no independent source SHA administrator seal or release approval has been issued. No Private Kotlin, sensitive metadata, signing files, logo/audio or Git ancestry was transferred.

**Readiness rubric:** eight weighted Public build/security process gates total **34.5/100% indicative only**, unchanged (Public history 15; synthetic CI 10; Private full scan 0; branch rules 0; actual resolved rights 0; draft snapshot handoff 4.5; real Android/Wear tests 0; evidence reports 5). This is NOT functional E-Clock phone/Wear MVP completion.
