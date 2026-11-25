# Status — 2026-11-25T07:14Z

## UNVERIFIED claims
- The ubrn RustBuffer size_t/u64 mismatch on armv7 causes the run-5 SIGSEGV (crash-triage.md). The mismatch itself is verified; the causal link is not.
- The mechanism by which a null future handle reaches rust_future_free_pointer (crash-triage.md).
- Delta installer, on the real device (delta-installer.md): toybox `tail -c +N file | head -c M` through rish seeks and streams correctly for 100+ MB runs (tested only with GNU tools and a fake rish).
- Delta installer: the real release redirect (github.com → signed CDN URL) honours a single Range on the resolved URL and gives a matching Content-Range (single ranges were seen to work earlier; this exact code path ran only against a mock server).
- Delta installer: seed entries with matching CRC/sizes have byte-identical local-header regions in the new APK (guarded by the final sha256 and automatic full-download fallback; the reuse fraction is unknown until a real dry run).
- Delta installer: python3 (stdlib only) is available in Termux on the tablet, and the fish wrapper parses (fish was not installed in the Claude workspace, so only the Python was syntax-checked).
- `pm install -r -S` of run 6 over run 5 succeeds (same signing key assumed; not tried).

## Open questions
- Does run 6 (RustBuffer fix) launch past the ~5 s crash point?
- If not: what do the run-6 crash pcs symbolicate to with the unstripped lib?
- What fraction of run 6 can be reused from the installed run-5 APK? (`filen_delta apk-7153fce-run6 --dry-run` reports it.)

## Answered (2026-11-24 source read)
- Who calls rust_future_free_pointer: ubrn's generic `uniffiRustCallAsync` helper, in its `finally` block, for every pointer-returning async call (14 call sites in src/generated/filen_sdk_rs.ts).
- Same uniffi version in both libs: yes, 0.29.4. Not the cause.
- 32-bit pointer-width assumption: yes, in ubrn's C++ RustBuffer (size_t). Not in uniffi's handle encoding.

## Next steps (ordered)
1. DONE: run 6 (id 45346897158) succeeded at 2026-11-24T08:36Z; assets in build-ci.md.
2. DONE: delta installer written and locally tested (tools/delta/). Clone the repo to ~/dev/filen-apk-armv7 on the tablet and source tools/delta/filen_delta.fish, then `filen_delta apk-7153fce-run6 --dry-run`, then without `--dry-run`. — Sonnet
3. After install: launch and capture logs: logcat -c, `monkey -p io.filen.app -c android.intent.category.LAUNCHER 1`, wait ~10 s, grep log. Confirm APK ABIs and primaryCpuAbi. — Sonnet
4. If it still crashes: download libfilen_sdk_rs-armv7-unstripped.so.gz (to the Claude workspace, not the tablet) and symbolicate the tombstone pcs. — Opus
