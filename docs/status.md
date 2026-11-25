# Status — 2026-11-25T22:54Z

## UNVERIFIED claims
- The ubrn RustBuffer size_t/u64 mismatch on armv7 causes the run-5 SIGSEGV (crash-triage.md). The mismatch itself is verified; the causal link is not.
- The mechanism by which a null future handle reaches rust_future_free_pointer (crash-triage.md).
- Installer paths not yet exercised on the tablet: the mid-assembly seed-failure fallback, the full-download fallback, and the progress bar (the 2026-11-25T10:47Z run predates it; the in-place redraw on a terminal is untested).
- The loopback adb connection survives until reboot or until adb over TCP is restarted; after that the installer tries `adb connect localhost:5555` once and otherwise falls back to a full download.

## Open questions
- Does run 6 (RustBuffer fix) launch past the ~5 s crash point?
- If not: what do the run-6 crash pcs symbolicate to with the unstripped lib?

## Answered (2026-11-25 first real installer run, 10:47Z)
- The delta rebuild of run 6 from the installed run-5 base.apk matched the release sha256 (so seed entries with matching CRC/sizes do have byte-identical regions) and used the real release redirect with single Range requests: 77.9 MB copied from the seed, 76.4 MB fetched, 76.5 MB over the network in 9 requests (about half of 154.3 MB).
- `adb -s emulator-5554 install -r` of run 6 over run 5 succeeded (`Success`); the package then reports primaryCpuAbi=armeabi-v7a, versionName 4.0.19.

## Answered (2026-11-25 latency benchmark, 10:03Z)
- adb per-call round trip ≈ 110 ms vs rish ≈ 1,000 ms on the tablet; adb is the default channel for device commands (decisions.md).

## Answered (2026-11-25 adb transport test, 09:55Z)
- adb `exec-out` is reliable for bulk data: three 20 MB slices hash-matched and the whole 269,401,212-byte seed streamed in 9 s with a matching sha256. The installed run-5 base.apk is byte-identical to the run-5 release asset (sha256 409ae6cb…).
- adb lists the tablet only as `emulator-5554`; the installer selects it automatically.

## Answered (2026-11-25 tablet transport test, 08:37Z)
- rish bulk stdout is unreliable: 20 MB reads arrive split across stdout/stderr with bytes lost, in all four variants tried; hashes never match. Text answers from rish land on stdout or stderr unpredictably. The delta installer's `tail|head` seed reads therefore cannot work as written.
- Staging through shared storage works: rish `dd` into /sdcard/Download, Termux reads ~/storage/downloads; 19,922,944 bytes, hash match, 5 s, probe removed.

## Answered (2026-11-25 tablet run)
- python3 (stdlib) is available in Termux and the fish wrapper parses and runs; REST release-metadata and free-space preflight work on the tablet (dry run at 2026-11-25T08:08Z).

## Answered (2026-11-24 source read)
- Who calls rust_future_free_pointer: ubrn's generic `uniffiRustCallAsync` helper, in its `finally` block, for every pointer-returning async call (14 call sites in src/generated/filen_sdk_rs.ts).
- Same uniffi version in both libs: yes, 0.29.4. Not the cause.
- 32-bit pointer-width assumption: yes, in ubrn's C++ RustBuffer (size_t). Not in uniffi's handle encoding.

## Next steps (ordered)
1. DONE: run 6 (id 45346897158) succeeded at 2026-11-24T08:36Z; assets in build-ci.md.
2. DONE: installer switched from rish to adb (seed reads and install). If adb is unavailable the installer falls back to a full download (no seed); rish cannot substitute because it shares adb's bootstrap.
3. DONE: run 6 delta-installed on the tablet (2026-11-25T10:47Z).
4. Launch and capture logs: logcat -c, `monkey -p io.filen.app -c android.intent.category.LAUNCHER 1`, wait ~10 s, grep log. Confirm APK ABIs and primaryCpuAbi. — Sonnet
5. If it still crashes: download libfilen_sdk_rs-armv7-unstripped.so.gz (to the Claude workspace, not the tablet) and symbolicate the tombstone pcs. — Opus
