# Crash triage — run 5

## Fixed
- UnsatisfiedLinkError (run 3): libfilen-sdk-rs.so missing because @filen/sdk-rs ships only arm64-v8a and x86_64 libs. FIXED in run 5: armv7 libfilen_sdk_rs.so loads; Rust runtime starts ("Creating Tokio runtime", "Auth file not found"); MainActivity displays at +5.7 s.

## Current crash (observed)
- ~5 s after launch: SIGSEGV, code 1 SEGV_MAPERR, fault addr 0xfffffff8.
- Thread mqt_v_js (React Native JS thread).
- Frame #00 in base.apk at offset 0x53d0000: ffi_filen_sdk_rs_rust_future_free_pointer+32.
- Registers: r0=0, ip=0xfffffff8, pc=700af02c, lr=77f2acf9.
- Backtrace stops after frame #00 (frame #01 pc 00000001 <unknown>); no unwind info.
- No ReactNativeJS or uniffi log lines in the crashed run.

## Hypothesis — UNVERIFIED
JS calls rust_future_free with a null (0) handle; on 32-bit, Arc::from_raw computes 0 - 8 = 0xfffffff8. Candidate causes:
1. A failed async call whose handle was never valid.
2. JS bindings vs Rust lib uniffi version mismatch (incl. libfilen_mobile_native_cache vs sdk lib).
3. Handle truncation / pointer-width assumption on 32-bit.

## Ruled out
- Future-handle type in the bindings: in @filen/sdk-rs@0.5.34, cpp/generated/filen_sdk_rs.cpp declares future handles as uint64_t and src/generated/filen_sdk_rs-ffi.ts types them as bigint. Matches the uniffi ABI.

## Diagnostic limits
- Tombstones unreadable via rish; logcat -b crash and the DEBUG tag give only frame #00.
