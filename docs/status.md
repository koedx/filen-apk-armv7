# Status — 2026-11-24T06:55Z

## UNVERIFIED claims
- Run 5 crash cause: null future handle freed → 0 - 8 = 0xfffffff8 on 32-bit (crash-triage.md).
- Candidate causes: failed async call with invalid handle; uniffi version mismatch between JS bindings and Rust lib(s); 32-bit handle truncation.

## Open questions
- Who calls rust_future_free_pointer in src/generated/filen_sdk_rs.ts, and under what failure path?
- Are libfilen_mobile_native_cache and libfilen_sdk_rs built against the same uniffi version?
- Any usize/u64/pointer-width assumption in filen-rs that breaks on 32-bit?

## Next steps (ordered)
1. Read source (no CI cost): filen-rs at tag filen-js@0.5.34 and filen-ts packages/filen-mobile. Answer the open questions above. — Opus
2. If still unclear: CI run with debug symbols (CARGO_PROFILE_RELEASE_DEBUG=1, publish unstripped libfilen_sdk_rs.so as a release asset) plus JS-side error logging. — Opus
3. Write the delta installer (delta-installer.md). — Sonnet
4. Re-dispatch CI with the fix (ABI patch ac73f55 already in), confirm APK ABIs, install, launch, capture logs: find package, logcat -c, `monkey -p io.filen.app -c android.intent.category.LAUNCHER 1`, wait ~10 s, grep log. — Sonnet
