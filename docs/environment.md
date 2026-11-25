# Environment

## Target device
- Keefe Score 7T, MediaTek MT8168, 32-bit armv7 userland (armeabi-v7a), Android 10 / API 29, ~1.9 GB RAM.
- Storage-constrained; preflight free space before any download or install.

## Tooling on device
- Termux + fish, inside tmux (single ~/.tmux.conf). tmark/tgrab fish helpers capture output for pasting back.
- Shizuku + rish for shell-level (ADB-equivalent) access. adb (android-tools 37.0.0p1) is also installed and connects to the tablet itself over loopback; the bootstrap is the same as Shizuku's (user-stated). `adb devices` lists it as `emulator-5554` (model:711, device:tb8168p1_bsp), an alias for the loopback adbd on port 5555 (a `localhost:5555` entry may also appear); address it with `adb -s <serial>`.
- adb bulk transfer is reliable (tablet test, 2026-11-25T09:55Z): `adb exec-out` returned three 20 MB slices and the whole 269,401,212-byte base.apk with hashes matching the device-side sha256, 9 s for the full file.
- Per-call latency (tablet benchmark, 2026-11-25T10:03Z, 10 trivial commands, two rounds each): adb ≈ 110 ms, rish ≈ 1,000 ms (≈10x slower, consistent with a Java client start per call). Default channel for device shell commands is therefore adb; rish remains a fallback when adb is not connected.
- rish bulk output is NOT reliable on stdout (tablet test, 2026-11-25T08:37Z): 20 MB reads (`tail|head`, `dd`, with `| cat` or a trailing sleep) arrived split across stdout and stderr with bytes lost (e.g. 9.6 MB + 7.6 MB of 20 MB); every hash mismatched the device-side hash. Small outputs are fine.
- rish text answers (`pm path`, `stat`) arrive on stdout or stderr, varying between calls; read both.
- Reliable bulk path (verified, 20 MB, hash match, 5 s): rish writes into shared storage (`dd ... of=/sdcard/Download/<file>`), Termux reads it from ~/storage/downloads, then both sides remove it.
- /data/tombstones is not readable via rish (Permission denied).
- Installing an APK from /sdcard fails (system_server SELinux denial). Install with adb's streamed install: `adb -s <serial> install -r <apk>` (UNVERIFIED on this tablet). The earlier `cat apk | rish -c "pm install -r -S <bytes>"` is not used for large APKs because rish bulk data is unreliable.

## Network
- Throttled Bluetooth-PAN; internet not always available. Scripts must have an offline path and go online only for the step that needs it.

## Build policy
- Never compile on device. All builds run on GitHub CI (account koedx). See build-ci.md.
