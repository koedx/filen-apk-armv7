# Delta installer — design (adb transport; first real run succeeded 2026-11-25T10:47Z)

Code: `tools/delta/filen_delta.py` (stdlib-only Python glue) and `tools/delta/filen_delta.fish` (wrapper function `filen_delta`). On the tablet: clone the repo to ~/dev/filen/filen-apk-armv7 and `git pull --ff-only` to update; source tools/delta/filen_delta.fish. Needs python3 and adb (android-tools) connected to the tablet itself. Verified APKs are cached outside the working tree in ~/dev/filen/apks (override: FILEN_DELTA_APKS; script dir override: FILEN_DELTA_HOME).

## Facts it relies on
- Release CDN: single-range requests work (206); multi-range returns 501.
- adb `exec-out` streams the seed bit-exactly (three 20 MB slices and the whole 269 MB seed, hash-matched, 9 s; environment.md). rish bulk stdout is unreliable and is not used.
- The installed run-5 base.apk is byte-identical to the run-5 release asset (same sha256).
- Run 3 → run 5: 158.4 MB byte-identical (per-entry CRC), 110.2 MB changed in 9 contiguous runs, plus zip index and signing block ≈ 12 range requests. x86_64 libs were unchanged (no delta cost); dropping them saves ~73 MB of APK/flash only.

## Usage
`filen_delta TAG [--dry-run] [--no-install] [--full]` — TAG is the release tag (e.g. apk-7153fce-run6). Python logs to stderr with section banners; stdout carries only the final APK path. Exit codes: 0 ok, 2 preflight/usage, 3 network, 4 verification failed.

## Design
1. Offline path first: if `<tag>-Filen-armv7.apk` and its `.sha256` sidecar exist and verify, skip all network and go to install.
2. Release metadata via REST (`/repos/koedx/filen-apk-armv7/releases/tags/<tag>`): asset size and `sha256:` digest.
3. Preflight: free space in the cache dir ≥ APK size + 64 MB (≈ 0.33 GB, under 1 GiB).
4. Plan: seed = installed base.apk (`adb shell pm path io.filen.app`; data via `adb exec-out "tail -c +N file | head -c M"`; device = a `...:5555` serial if listed, else the only online device (the loopback adbd often appears as emulator-5554), else `adb connect localhost:5555` is tried once; several unrelated devices need `--serial`). Read the zip central directory of seed and release APK (EOCD + CD + APK Sig Block boundary). An entry's byte region is reusable when name, CRC, sizes, method, flags and region length all match. Regions contiguous in both files are coalesced; copy runs under 64 KiB are fetched instead. Everything else (changed entries, signing block, central directory, EOCD) is fetched, one Range request per gap. zip64 is not supported (falls back to full download).
5. Assemble sequentially into `.part`, hashing as it writes. Resolve the release redirect once; re-resolve and resume from the last byte on error (5 tries). Each response must be 206 with a matching Content-Range.
6. Verify size and sha256 against the digest. On mismatch the assembled file is discarded and a full resumable download (Range from the current size) is used. A failed final verification keeps the `.part` for inspection (exit 4). Success renames to the final name and writes the sidecar.
7. Install (fish wrapper): confirmation prompt, then `adb -s <serial> install -r <apk>` (streamed install), then show package path, versionName, primaryCpuAbi.
8. Any failure reading the seed (adb missing, no or several devices, short read) discards the work and falls back to the full download; a failed delta never installs.

## Constraints
- Never deletes cached APKs; asks before installing; verbose output; downloads and assembly show a progress bar with percent, MB done/total, speed and ETA (redrawn in place on a terminal, one line per 10% otherwise); no temp files other than `.part` and the sidecar.
- No GitHub token is used; the repo's release assets must be publicly downloadable.

## Verified on the tablet
Run 6 (2026-11-25T10:47Z): delta rebuild from the installed run-5 base.apk, 77.9 MB copied and 76.5 MB fetched in 9 requests, sha256 matched the release digest, `adb install -r` Success, primaryCpuAbi=armeabi-v7a. The progress bar, the mid-assembly seed-failure fallback and the full-download fallback have not run on the tablet.

## Verified (local test only)
Synthetic APKs with an APK Sig Block, a Range-capable mock server and a fake adb (only emulator-5554; :5555 plus alias; ambiguous devices; truncated exec-out; adb missing; device appearing after `adb connect`; fish end-to-end with install): delta rebuild byte-identical (3.0 of 8.3 MB fetched, 7 requests); offline cache path with the server down; corrupt seed falls back to full download and verifies; bad digest exits 4; dry run; missing seed falls back. See status.md for what is still UNVERIFIED on the real device and CDN.
