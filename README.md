# Embasic E-Clock — Public Build Infrastructure

This separate public repository is reserved for **security-reviewed, zero-private-history Android and Wear OS CI**. It is not the private development repository. Do not mirror, merge, or push private Git history, secrets, user data, signing keys or unapproved third-party assets here.

**STATUS: NO-GO — Kotlin source publication and APK builds blocked pending private Gitleaks/PII/license/source audit.**

Architecture to preserve: `app-phone`, `app-wear`, `core:model`, `core:alarm`, `core:data`, `core:sync`; Kotlin, Jetpack Compose, Compose for Wear OS, Gradle Kotlin DSL, Room, DataStore, Coroutines/Flow, Wearable Data Layer, AlarmManager and local-first alarms.

Build verification must independently run Android phone, Wear OS, shared-core unit tests and lint on an Ubuntu GitHub-hosted runner after source audit. Real-device tests remain separate. No production signing or fake PASS statuses.

GitHub Actions is intentionally fail-closed until a source snapshot is fully audited and approved. The repository's initial commit is a clean public-only bootstrap; future public commits must not import private commit ancestry.
