# Environment

## Target device
- Keefe Score 7T, MediaTek MT8168, 32-bit armv7 userland (armeabi-v7a), Android 10 / API 29, ~1.9 GB RAM.
- Storage-constrained; preflight free space before any download or install.

## Tooling on device
- Termux + fish, inside tmux (single ~/.tmux.conf). tmark/tgrab fish helpers capture output for pasting back.
- Shizuku + rish for shell-level (ADB-equivalent) access.
- rish passes binary data cleanly in both directions (sha256 verified on stdout and stdin).
- /data/tombstones is not readable via rish (Permission denied).
- Installing an APK from /sdcard fails (system_server SELinux denial). Stream installs instead:
  `cat apk | rish -c "pm install -r -S <bytes>"`.

## Network
- Throttled Bluetooth-PAN; internet not always available. Scripts must have an offline path and go online only for the step that needs it.

## Build policy
- Never compile on device. All builds run on GitHub CI (account koedx). See build-ci.md.
