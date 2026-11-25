# Status — 2026-11-25T08:49Z

## UNVERIFIED claims
- The ubrn RustBuffer size_t/u64 mismatch on armv7 causes the run-5 SIGSEGV (crash-triage.md). The mismatch itself is verified; the causal link is not.
- The mechanism by which a null future handle reaches rust_future_free_pointer (crash-triage.md).
- Delta installer: the real release redirect (github.com → signed CDN URL) honours a single Range on the resolved URL and gives a matching Content-Range (single ranges were seen to work earlier; this exact code path ran only against a mock server).
- Delta installer: seed entries with matching CRC/sizes have byte-identical local-header regions in the new APK (guarded by the final sha256 and automatic full-download fallback; the reuse fraction is unknown until a real dry run).
- `pm install -r -S` of run 6 over run 5 succeeds (same signing key assumed; not tried).
- Streaming a ~154 MB APK into `pm install -S` over rish stdin arrives intact (only a small payload was checked earlier).
- Staging a full 269 MB seed copy through /sdcard/Download works like the 20 MB probe did (not tried at full size).

## Open questions
- Does run 6 (RustBuffer fix) launch past the ~5 s crash point?
- If not: what do the run-6 crash pcs symbolicate to with the unstripped lib?
- What fraction of run 6 can be reused from the installed run-5 APK? (`filen_delta apk-7153fce-run6 --dry-run` reports it.)

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
2. Rework the seed transport: stage the installed base.apk into ~/storage/downloads via rish (preflight ~0.5 GB free), read it with normal file seeks, remove it after. Awaiting user confirmation (structural change). — Sonnet
2b. Test the install direction with the real APK (stdin streaming vs staging to /data/local/tmp). — Sonnet
3. After install: launch and capture logs: logcat -c, `monkey -p io.filen.app -c android.intent.category.LAUNCHER 1`, wait ~10 s, grep log. Confirm APK ABIs and primaryCpuAbi. — Sonnet
4. If it still crashes: download libfilen_sdk_rs-armv7-unstripped.so.gz (to the Claude workspace, not the tablet) and symbolicate the tombstone pcs. — Opus
