# Environment

## Target device
- Keefe Score 7T, MediaTek MT8168, 32-bit armv7 userland (armeabi-v7a), Android 10 / API 29, ~1.9 GB RAM.
- Storage-constrained; preflight free space before any download or install.

## Tooling on device
- Termux + fish, inside tmux (single ~/.tmux.conf). tmark/tgrab fish helpers capture output for pasting back.
- Shizuku + rish for shell-level (ADB-equivalent) access.
- rish bulk output is NOT reliable on stdout (tablet test, 2026-11-25T08:37Z): 20 MB reads (`tail|head`, `dd`, with `| cat` or a trailing sleep) arrived split across stdout and stderr with bytes lost (e.g. 9.6 MB + 7.6 MB of 20 MB); every hash mismatched the device-side hash. Small outputs are fine.
- rish text answers (`pm path`, `stat`) arrive on stdout or stderr, varying between calls; read both.
- Reliable bulk path (verified, 20 MB, hash match, 5 s): rish writes into shared storage (`dd ... of=/sdcard/Download/<file>`), Termux reads it from ~/storage/downloads, then both sides remove it.
- UNVERIFIED: the stdin direction for large payloads (`cat apk | rish -c "pm install -r -S <bytes>"` with a ~154 MB APK); only a small payload was checked earlier.
- /data/tombstones is not readable via rish (Permission denied).
- Installing an APK from /sdcard fails (system_server SELinux denial). Stream installs instead:
  `cat apk | rish -c "pm install -r -S <bytes>"`.

## Network
- Throttled Bluetooth-PAN; internet not always available. Scripts must have an offline path and go online only for the step that needs it.

## Build policy
- Never compile on device. All builds run on GitHub CI (account koedx). See build-ci.md.
