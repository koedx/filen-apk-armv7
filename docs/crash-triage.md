# Crash triage — run 5

## Fixed
- UnsatisfiedLinkError (run 3): libfilen-sdk-rs.so missing because @filen/sdk-rs ships only arm64-v8a and x86_64 libs. FIXED in run 5: armv7 libfilen_sdk_rs.so loads; Rust runtime starts ("Creating Tokio runtime", "Auth file not found"); MainActivity displays at +5.7 s.

## Current crash (observed, run 5)
- ~5 s after launch: SIGSEGV, code 1 SEGV_MAPERR, fault addr 0xfffffff8.
- Thread mqt_v_js (React Native JS thread).
- Frame #00 in base.apk at offset 0x53d0000: ffi_filen_sdk_rs_rust_future_free_pointer+32.
- Registers: r0=0, ip=0xfffffff8, pc=700af02c, lr=77f2acf9.
- Backtrace stops after frame #00 (frame #01 pc 00000001 <unknown>); no unwind info.
- No ReactNativeJS or uniffi log lines in the crashed run.

## Root cause candidate: RustBuffer ABI mismatch on 32-bit
Found by reading the source (2026-11-24, no CI run).

Verified from source and by compiling:
- The ubrn version filen-ts pins (Enduriel/uniffi-bindgen-react-native@e0282ad) declares `struct RustBuffer { size_t capacity; size_t len; uint8_t *data; }` in cpp/includes/RustBuffer.h. The APK's C++ (cpp/generated/filen_sdk_rs.cpp) compiles against that header, which CMake finds through `require.resolve('uniffi-bindgen-react-native')`.
- uniffi_core 0.29.4 (the version filen-rs filen-js@0.5.34 locks) declares RustBuffer as `#[repr(C)] { capacity: u64, len: u64, data: *mut u8 }`.
- On arm64 both layouts are 24 bytes and identical. On armv7 the C++ one is 12 bytes (align 4) and the Rust one is 24 bytes (align 8). A clang `-target` check confirms that a `sizeof == 24 && alignof == 8` assertion fails only on armv7 with the unpatched struct.
- RustBuffer carries every string and serialized argument or return value, and it is embedded in RustCallStatus. So on 32-bit, by-value arguments are passed in the wrong registers or stack slots, and Rust writes 24-byte returns into 12-byte C++ slots.
- Upstream ubrn fixed exactly this in jhugman/uniffi-bindgen-react-native d3e421a (2026-02-27), "Use uint64_t for RustBuffer fields to fix 32-bit ARM crash (#344)", originally from PR #313. The pinned fork commit predates it.

UNVERIFIED:
- That this mismatch causes the run-5 SIGSEGV.
- The exact path to a null handle at free time. Reasoning: uniffi's `rust_future_poll` also dereferences the handle (`get_arc`), and the JS helper (`uniffiRustCallAsync`) passes the same bigint to poll and free. A null handle reaching free without crashing in poll therefore suggests stack or argument corruption around the async call, which fits the mismatch.

Fix in CI: patch RustBuffer.h to `uint64_t` after `pnpm install`, plus a `static_assert` guard (see build-ci.md).

## Ruled out
- Future-handle type in the bindings: in @filen/sdk-rs@0.5.34, cpp/generated/filen_sdk_rs.cpp declares future handles as uint64_t and src/generated/filen_sdk_rs-ffi.ts types them as bigint. Matches the uniffi ABI.
- Handle truncation on 32-bit: uniffi 0.29.4 `Handle` is `repr(transparent) u64` holding the zero-extended pointer. ubrn `Bridging<uint64_t>` converts losslessly through JSI BigInt (`fromUint64` / `asUint64`).
- uniffi version mismatch: filen-rs filen-js@0.5.34 locks uniffi 0.29.4 everywhere, and the armv7 SDK lib is built from the same tag as the npm bindings. libfilen_mobile_native_cache is bound through uniffi's Kotlin bindings, which are generated from the built lib at prebuild time. Those use 64-bit RustBuffer fields, so this bug doesn't affect them.

## Diagnostic limits
- Tombstones unreadable via rish; logcat -b crash and the DEBUG tag give only frame #00.
- From run 6 on, the unstripped SDK lib (line tables) is published as a release asset for offline symbolication of crash pcs.
