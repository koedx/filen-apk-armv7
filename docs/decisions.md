# Decision log (append-only — never edit past entries)

Dates for entries up to 2026-11-24T06:20Z come from commit and run timestamps or from the session that made the decision. Where only a window is known, the entry is stamped with the latest possible time and says so.

## 2026-11-19T10:11Z — Build only on GitHub CI; lower minSdk to 29 (commit dba731f)
What: All compilation runs on GitHub Actions (koedx/filen-apk-armv7, workflow_dispatch); the workflow patches upstream minSdk 31 → 29 and adds armeabi-v7a.
Why: Tablet is 32-bit, API 29, ~1.9 GB RAM, storage- and bandwidth-limited; upstream ships no 32-bit build and requires API 31.
Supersedes: —

## 2026-11-19T10:44Z — Use the runner's default NDK r27 (commit 8d6aec4)
What: Stop forcing NDK 30.
Why: NDK 30 broke the heif-decoder bindgen step (run 1 failure).
Supersedes: forced NDK 30.

## 2026-11-19T11:15Z — Install the wild linker in CI (commit 38d206c)
What: Install wild-linker explicitly.
Why: filen-rs host-side builds link with it (run 2 failure).
Supersedes: —

## 2026-11-23T06:48Z — Build the armv7 SDK lib from the matching filen-rs tag (commit 32a68da)
What: CI builds libfilen_sdk_rs.so for armeabi-v7a from filen-rs tag `filen-js@<npm version>` and adds armeabi-v7a to the sdk-rs abiFilters.
Why: Run 3 crashed with UnsatisfiedLinkError; the npm package ships only 64-bit libs. The submodule pin lags the npm bindings, so building from it would mismatch.
Supersedes: relying on the npm package's prebuilt libs.

## 2026-11-24T06:01Z — Delta installer via single-range requests; zsync rejected (decided between 2026-11-23T07:17Z and this time)
What: Rebuild new APKs from the installed base.apk plus single Range fetches; stream install through rish.
Why: CDN rejects multi-range (501), which rules out zsync; ~59% of bytes are reusable between runs; /sdcard installs fail under SELinux; rish verified binary-clean both ways.
Supersedes: full APK download per run; zsync.

## 2026-11-24T06:01Z — Use GitHub REST, not GraphQL (observed no later than this time)
What: Dispatch and query via `gh api` REST endpoints.
Why: GraphQL is blocked in Claude sessions.
Supersedes: `gh workflow run` (GraphQL-backed).

## 2026-11-24T06:20Z — Ship armeabi-v7a only (commit ac73f55)
What: ANDROID_ABIS = ["armeabi-v7a"], sdk-rs abiFilters "armeabi-v7a".
Why: Target is armv7 only; x86_64 libs added ~73 MB of APK/flash. No delta-bandwidth gain (those libs were unchanged between runs).
Supersedes: dual x86_64 + armeabi-v7a builds (runs 1–5).

## 2026-11-24T06:23Z — Do not dispatch ac73f55 alone
What: Hold the ABI-only build until a crash fix or diagnostic change is ready.
Why: A ~2 h run would reproduce the same run-5 crash.
Supersedes: —

## 2026-11-24T06:55Z — Spec lives in repo docs/, mirrored to the Project
What: Canonical spec in koedx/filen-apk-armv7 docs/; claude.ai Project "filen: armv7 apk" keeps a mirror under spec/, updated in the same session.
Why: Versioned next to the code; the Project copy loads automatically at session start.
Supersedes: handover-card-only state.
