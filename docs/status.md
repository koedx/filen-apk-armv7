# Status — 2026-11-24T07:20Z

## UNVERIFIED claims
- The ubrn RustBuffer size_t/u64 mismatch on armv7 causes the run-5 SIGSEGV (crash-triage.md). The mismatch itself is verified; the causal link is not.
- The mechanism by which a null future handle reaches rust_future_free_pointer (crash-triage.md).

## Open questions
- Does run 6 (RustBuffer fix) launch past the ~5 s crash point?
- If not: what do the run-6 crash pcs symbolicate to with the unstripped lib?

## Answered (2026-11-24 source read)
- Who calls rust_future_free_pointer: ubrn's generic `uniffiRustCallAsync` helper, in its `finally` block, for every pointer-returning async call (14 call sites in src/generated/filen_sdk_rs.ts).
- Same uniffi version in both libs: yes, 0.29.4. Not the cause.
- 32-bit pointer-width assumption: yes, in ubrn's C++ RustBuffer (size_t). Not in uniffi's handle encoding.

## Next steps (ordered)
1. Commit the workflow fix and dispatch run 6 on main (ac73f55 ABI change + RustBuffer patch + unstripped lib). — Sonnet
2. While run 6 builds (~2 h): write the delta installer (delta-installer.md). — Sonnet
3. Verify run-6 assets (size, sha256), install, launch, capture logs: find package, logcat -c, `monkey -p io.filen.app -c android.intent.category.LAUNCHER 1`, wait ~10 s, grep log. Confirm APK ABIs. — Sonnet
4. If it still crashes: download libfilen_sdk_rs-armv7-unstripped.so.gz (to the Claude workspace, not the tablet) and symbolicate the tombstone pcs. — Opus
