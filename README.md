# filen-apk-armv7

Unofficial CI that builds the Filen Android app ([`filen-ts`](https://github.com/FilenCloudDienste/filen-ts),
`packages/filen-mobile`) for 32-bit ARM (`armeabi-v7a`) with minSdk lowered from 31 to 29 (Android 10).

- Run: Actions tab -> `build-filen-apk-armv7` -> Run workflow, or `gh workflow run build.yml -R koedx/filen-apk-armv7`.
- Output: a GitHub Release with `Filen-armv7.apk` and `armv7-android10.diff` (the patch).
- Signing: debug key unless a keystore is configured. Personal sideloading only.
- Optional repo secret `SECURE_STORE_UNSECURE_FALLBACK_ENCRYPTION_KEY` keeps the fallback key stable across builds.
- Status: UNVERIFIED until a build is installed and tested on the device.

Upstream is AGPL-3.0; this repo only contains the build workflow.
