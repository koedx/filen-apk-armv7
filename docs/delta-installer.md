# Delta installer — design (not yet written)

## Facts it relies on
- Release CDN: single-range requests work (206); multi-range returns 501.
- rish streams binary cleanly; install via stdin with explicit size.
- Run 3 → run 5: 158.4 MB byte-identical (per-entry CRC), 110.2 MB changed in 9 contiguous runs, plus zip index and signing block ≈ 12 range requests. x86_64 libs were unchanged (no delta cost); dropping them saves ~73 MB of APK/flash only.

## Design
1. Seed: locate installed APK (`pm path io.filen.app`) and stream it via `rish -c "cat <path>"`.
2. Read the new APK's zip central directory via single Range requests.
3. Copy unchanged entries from the seed; fetch changed byte runs with single ranges. Resolve the release redirect once; re-resolve on URL expiry; retry.
4. Verify size and sha256 against the release asset digest.
5. Fallback: full resumable download (curl -C -).
6. Stream install: `cat apk | rish -c "pm install -r -S <bytes>"`.

## Constraints
- Fish function wrapping Python glue is acceptable.
- Preflight free space; keep the APK on failure; ask before deleting; verbose output with section banners; no temp cruft.
