# Embasic E-Clock — Public Development Repository

> **Decision (27 October 2026):** `ftmstr/Embasic-E-Clock-Build` is the **only active development repository** for Embasic E-Clock. The former `ftmstr/E-Clock` Private repository is **retired from active development**: do not fetch its code, push to it, mirror it, merge it, or use its source/history/assets as an input. The owner may independently delete it later; **this project does not perform or request deletion**.

## Current, accurately verified state

- Public `main` currently contains security/CI tooling and documents only; **there is no compiled Android phone or Wear OS application, no verified APK, and no completed device testing**.
- The Public `main` branch has **not yet been protected** ([blocking Issue #2](https://github.com/ftmstr/Embasic-E-Clock-Build/issues/2)). Its Android build workflow is intentionally **NO-GO** until independently reviewed source/build, licensing and security gates are satisfied.
- Prior synthetic unit-test PASS results concern the **Public tooling** only. They do not certify Android application behavior.
- Existing `tools/private_audit_preflight.py` and Private-to-Public export documentation are **legacy quarantine procedures**, not development dependencies. Do not mark their Private scans `PASS` or execute them for the new Public-only project.

## New source-of-truth workflow: original implementation only

All future application code will be **written anew**, using the Embasic E-Clock product requirements and publicly documented Android/Wear OS APIs. Do **not** import private Git commits, files, copy/pasted source, build caches, third-party media, secret values, user/identity data, previous Private reports or signing credentials. Original code committed to a Public GitHub branch is immediately public; review source, dependency licenses, security, assets and file metadata **before each commit**.

1. **Design first.** Maintain a technical plan, module tree, domain and storage schemas, Data Layer sync contract, ring/STOP/SNOOZE state machine and Architecture Decision Records. See [Public-only implementation decision](docs/PUBLIC_SNAPSHOT_HANDOFF.md).
2. **Review + protection.** Work on a new feature branch and draft PR. The repository owner must configure effective `main` protection/rulesets with required review and required synthetic CI, while prohibiting force pushes/deletion and restricting bypasses. Do not circumvent the fail-closed workflow to obtain a green Android build.
3. **Greenfield Gradle scaffold.** Produce buildable Kotlin Android + Wear modules with reproducible pinned dependencies, dependency/license inventory, reproducible Gradle verification and documented permissions. Never declare a code snapshot `APPROVED` on synthetic evidence alone.
4. **Vertical implementation:** local alarm CRUD and exact scheduling → ringing/STOP/SNOOZE → alarm groups → Wearable Data Layer conflict-safe sync → Wear OS UI → World Clock → Stopwatch → Timer → settings → migration, reliability and device testing.
5. **Evidence every gate.** Build, lint and unit/integration tests must actually run in GitHub Actions. Track `PASS`, `FAIL`, `SKIPPED`, `NOT RUN` separately; require paired physical-device testing of offline alarms, reboot, Doze and DST before calling the MVP complete.

## Architecture target

```text
app-phone/             Android phone / Jetpack Compose + Material 3
app-wear/              Wear OS / Compose for Wear OS
core/model/            UUID-based alarm, group, ring and timing contracts
core/alarm/            exact alarm scheduling, occurrence calculator, ring state
core/data/             Room, migrations, DataStore and local repositories
core/sync/             Wearable Data Layer (DataClient, MessageClient, Capability/Node)
```

Local-first invariants: each device stores and schedules locally; sync is idempotent and deterministic; alarm definitions are separate from `ringInstanceId` sessions; stale STOP/SNOOZE messages never change a later ring; offline operation must not depend on the paired device.

**Release status: NO-GO.** Public-only development is authorized by the repository choice, but neither Private source reuse nor automatic source/legal approval is implied. The old Private-history gate must be **replaced with an appropriate greenfield-source provenance gate through reviewed changes**, not falsely passed. Public security and legal checks, branch rules, verified Android builds and real device tests remain mandatory.
