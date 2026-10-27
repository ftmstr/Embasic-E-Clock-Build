# Public-only greenfield architecture and source provenance — ADR-001

**Adopted 27 October 2026 for the proposed Public-only development branch.** This document **supersedes** the former Private-to-Public snapshot handoff procedure. The previous text remains retrievable in Git history solely for audit. It is **not** an instruction or permission to export anything from `ftmstr/E-Clock`.

## Decision, repositories and safety boundary

- **Sole active source of truth:** `ftmstr/Embasic-E-Clock-Build` (**PUBLIC**). All subsequent original E-Clock source, tests and engineering documents must originate in this repository on reviewed feature branches.
- **Retired/unused:** `ftmstr/E-Clock` (**PRIVATE**). No further writes, read-based migrations, cloning, history imports, merges, cherry-picks, source/asset copying or reference to its commits for implementation. Only the owner may independently decide to delete the retired repository later. Nothing here triggers deletion.
- **Absolute exclusions:** historical commits, private Kotlin/XML/Gradle sources, caches, credentials, keystore, identifiable user or device data, old artifacts, logos, media and reports are **not** authorized for redistribution. Existing Public tooling is not evidence that any Private scan passed.
- **Status:** Public `main` currently contains **infrastructure only**, is not effectively branch-protected and does not yield an Android APK. Issue [#2](https://github.com/ftmstr/Embasic-E-Clock-Build/issues/2) stays **OPEN / BLOCKING**. Do not disable the security job or forge `SNAPSHOT-AUDIT.json` approval to get a green build.

## Module structure for the first original scaffold

```text
settings.gradle.kts
build.gradle.kts
gradle/libs.versions.toml
gradle.properties
app-phone/             Android application, Compose Material 3, navigation and notifications
app-wear/              Wear OS application, Compose for Wear OS, rotary/haptics
core/model/            shared Kotlin domain types + schemaVersion and contracts
core/alarm/            AlarmManager planning, local recurrence, ringing session orchestration
core/data/             Room tables/migrations, repositories, DataStore preferences
core/sync/             Data Layer envelope validation, reconciliation, idempotency
```

Native Kotlin, Coroutines/Flow, Room, DataStore, exact alarm-clock APIs and Wearable Data Layer. No separate hosted backend. Architecture is **local-first**: each phone/watch device stores and pre-schedules eligible alarms, continues during link loss and reconciles when reconnected.

## Domain model and storage contract (design before implementation)

| Model | Key fields / rules |
|---|---|
| `AlarmDefinition` | `id: UUID`, local hour/minute, label, enabled, repeat weekdays and optional one-shot date, zone/DST occurrence policy, sound, vibration, snooze enabled/minutes/count, ring target `PHONE/WATCH/BOTH`, optional `groupId` |
| `AlarmGroup` | `id: UUID`, label, explicit permanent enable state and distinct temporary-skip rule; per-alarm enabled flags not silently rewritten when a group is skipped |
| `RecordMetadata` | `schemaVersion`, `revision` (monotonic Lamport-style), `updatedAt` (observability only), `originDeviceId`, `isTombstone`; never resurrect a deleted UUID from stale state |
| `AlarmOccurrence` | occurrence UUID derived or persisted with definition UUID, due epoch, target and local scheduling version; calculate next occurrence with `java.time` and explicit timezone policy |
| `RingSession` | `ringInstanceId: UUID`, alarm ID, scheduled occurrence key, local target/device, state, snooze attempt and current due time; never treat this as the same object as the alarm definition |
| `WorldClockEntry` | local user entry UUID, city label and IANA `ZoneId`; maximum 20 entries, offline time calculation |
| `StopwatchSession` / `TimerSession` | stable IDs; stopwatch monotonic elapsedRealtime anchors; timers persisted wall-clock deadlines with boot/rebase handling; future-proof for multiple parallel timers |

Room migrations must be versioned and tested. Store per-device local preferences separately from globally synchronized preferences.

## Wearable Data Layer protocol (planned schema v1)

- `DataClient`: versioned durable alarm/group records, tombstones and reconciliation snapshots/deltas. Never require a live message to ensure a device's scheduled alarm exists.
- `MessageClient`: best-effort immediate `RING_STARTED`, `STOP`, `SNOOZE` actions. Envelope fields: `schemaVersion`, message ID, `ringInstanceId`, alarm UUID, origin device ID, action, occurrence identity and bounded timestamps/arguments.
- `NodeClient`/`CapabilityClient`: peer discovery and capability negotiation, **not** transport of large persistent state.
- Validate size, version, enum values, IDs, tombstone structure and stale message/session mismatch; reject malformed or replayed envelopes without crashing.
- Deterministic tie-breaking for concurrent alarm-definition edits: compare increasing `revision` first, then permanent tombstone priority at equal revision, then lexicographic `originDeviceId`. `updatedAt` is informational only because wall clocks may differ. A tombstoned UUID is not implicitly reused; deliberate recreation allocates a new UUID. Persist applied message IDs and reconcile after link restoration.
- Any future tombstone garbage-collection strategy must prove acknowledgement or bound risk of offline reappearance; default is retention until independently tested.

## Ring state machine and durability (planned)

```text
ENABLED/PLANNED --local AlarmManager trigger--> RINGING
RINGING --local STOP--> DISMISSED
RINGING --SNOOZE (budget available)--> SNOOZED --next local trigger--> RINGING
RINGING --timeout/rule--> DISMISSED
RINGING/SNOOZED --reboot/process recovery--> reconcile persisted session + next due
```

STOP and SNOOZE on a paired device coordinate only a **matching** `ringInstanceId` and occurrence. STOP must never cancel an unrelated later alarm. Each device performs its own local ring/schedule decision, and a configured cross-device STOP/SNOOZE is applied idempotently upon receipt. Prioritize locked-screen alarm usability and correct notification/permission handling.

## Architecture decisions and implementation order

- **ADR-001 (this document):** Public-only greenfield code, former Private inactive, zero reuse/import.
- **ADR-002:** independently scheduled phone/watch alarms; sync cannot be a prerequisite for the trigger.
- **ADR-003:** revision-based deterministic reconciliation with durable tombstones, idempotent messages and UUID ring sessions.
- **ADR-004:** exact alarm and full-screen notification behavior follow currently applicable **official** Android/Wear OS APIs, permissions and Play policy, independently verified before implementation; never claim a required permission based on guesswork.
- **ADR-005:** security release gates apply to **the new original Public source** and its actual artifacts. Legacy Private-history approval fields do **not** automatically become `VERIFIED`; redesign `tools/verify_snapshot.py` and CI via a reviewed PR for true greenfield provenance, required tests, dependency and third-party rights checks, without relaxing source/secret/PII protections.

Vertical sequence: **architecture/ADR → reproducible Gradle scaffold → local alarm CRUD/planning → ringing STOP/SNOOZE → groups → Data Layer sync → Wear OS UX → world clocks → stopwatch/laps → timer(s) → settings → data migrations and paired-device reliability**.

## Definition of each merge/build gate

1. Work only in a **Public feature branch** and reviewed PR. Repository owner must enable effective main protection, mandatory relevant CI check, PR review, force-push/deletion blocking and narrow bypass rules; verify actual GitHub readback.
2. Inspect each **new original source** and its commit contents for secrets/PII/unsafe files and third-party ownership; use a clean tracked-file manifest and an independent reviewer-managed SHA approval appropriate for this greenfield project. No fabricated approval and no Private clone dependency.
3. Resolve the **actual** Gradle plugin, runtime, compile, test and KSP/release dependencies; verify licenses, notices and binary hashes; capture exact CI evidence. Synthetic audit PASS is not Gradle build PASS.
4. Only when the source and CI gates genuinely pass, execute Android core/phone/Wear lint, unit tests and assembleDebug. Then evaluate real phone + watch offline/paired/reboot/Doze/DST/snooze/STOP acceptance tests. Never publish APK artifacts with unreviewed source or keystore.
5. Report `PASS`, `FAIL`, `NOT RUN`, `SKIPPED` separately, and do not label the project MVP complete without tested major features.

### Transition note

Older docs and scripts may still mention **Private-to-Public export**, including `tools/private_audit_preflight.py`, `tools/legacy_export_compatibility.py` and Private-history claims in `tools/verify_snapshot.py`. These remain **disabled as an active development strategy**. They will be retired/refactored only through reviewed Public changes with regression tests, preserving fail-closed source and license controls. Deleting the Private repo is expressly outside this workflow.
