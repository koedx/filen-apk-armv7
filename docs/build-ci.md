# Build and CI

## Repos
- koedx/filen-apk-armv7 — Android APK build (this project).
- koedx/filen-cli-armv7 — Filen CLI for armv7. DONE.

## Workflow
- .github/workflows/build.yml, trigger workflow_dispatch only (pushes do not start builds). Runs take ~2 h.
- Inputs: `ref` (filen-ts branch/tag/commit, default main), `min_sdk` (default 29; upstream is 31).
- Dispatch (REST; GraphQL is blocked in Claude sessions):
  `gh api -X POST repos/koedx/filen-apk-armv7/actions/workflows/build.yml/dispatches -f ref=main`
- Wait ~10 s after a push before dispatching.
- Toolchain as of run 5: runner default NDK r27, wild-linker 0.9.0, Rust nightly-2026-02-20.
- Validate YAML after every edit: `python3 -I -c "import yaml; yaml.safe_load(open('.github/workflows/build.yml'))"`.

## SDK native library
- CI builds libfilen_sdk_rs.so for armeabi-v7a from the filen-rs tag matching the installed npm version (`filen-js@<ver>`, currently 0.5.34), with features uniffi, heif-decoder, http-provider, cache, sync-engine, and copies it into the @filen/sdk-rs package jniLibs.

## ABI configuration (current, commit ac73f55 on main)
- ANDROID_ABIS = ["armeabi-v7a"]; sdk-rs abiFilters "armeabi-v7a"; release notes say "armeabi-v7a only".
- rustup target x86_64-linux-android still installed in the workflow (harmless, unused).
- ac73f55 has NOT been built yet; its first build should also carry the crash fix or diagnostics.

## Upstream versions
- @filen/sdk-rs@0.5.34 (npm), built from filen-rs tag filen-js@0.5.34.
- Pins uniffi-bindgen-react-native github:Enduriel/uniffi-bindgen-react-native#e0282ad3eb972eaea74225dcc06247b7a67204dd.

## Run history
| Run | Dispatched | Commit | Result |
|---|---|---|---|
| 1 | 2026-11-19T10:11Z | dba731f | failure (forced NDK 30 broke heif-decoder bindgen) |
| 2 | 2026-11-19T10:44Z | 8d6aec4 | failure (wild linker missing) |
| 3 | 2026-11-19T11:16Z | 38d206c | success — crashes on device (UnsatisfiedLinkError) |
| 4 | 2026-11-23T06:48Z | 32a68da | failure (sdk-rs package path lookup) |
| 5 | 2026-11-23T07:17Z | e59aceb | success — installed; SIGSEGV ~5 s after launch |

## Release assets
| Run | Tag | Asset | Bytes | sha256 |
|---|---|---|---|---|
| 5 (installed) | apk-7153fce-run5 | Filen-armv7.apk | 269401212 | 409ae6cbc0f077f140cbe65c4610b77c171070123581e18c6e7ff1a313338a17 |
| 3 | apk-09b67ce-run3 | Filen-armv7.apk | 238425656 | 2b3184c461a5f0cc3b8686c7d9d63b2dc984eb00ef343d5e67a415845ae31ccb |

- Digests are exposed by the API:
  `gh api repos/koedx/filen-apk-armv7/releases/tags/<tag> --jq '.assets[].digest'`

## Installed build
- io.filen.app, versionName 4.0.19, primaryCpuAbi=armeabi-v7a (run 5).
