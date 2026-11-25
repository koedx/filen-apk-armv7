#!/usr/bin/env python3
"""filen_delta.py - build a release APK from the installed APK plus single-range fetches.

Logs go to stderr (verbose, with section banners). The only stdout output is the
final verified APK path, so the fish wrapper can capture it.
Exit codes: 0 ok, 2 preflight/usage, 3 network, 4 verification failed.
"""
import argparse, hashlib, json, os, shutil, struct, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request

REPO = "koedx/filen-apk-armv7"
ASSET = "Filen-armv7.apk"
PKG = "io.filen.app"
MIN_COPY = 64 * 1024        # copy segments smaller than this are fetched instead
CHUNK = 1 << 20
MARGIN = 64 * 1024 * 1024   # free-space margin on top of the APK size


def log(msg=""):
    print(msg, file=sys.stderr, flush=True)


def banner(n, total, title):
    log(f"\n===== [{n}/{total}] {title} =====")


class Fail(Exception):
    def __init__(self, msg, code=3):
        super().__init__(msg)
        self.code = code


# ---------------------------------------------------------------- HTTP

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def http_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "filen-delta"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def resolve(url):
    """Follow redirects manually and return the final (signed) URL."""
    opener = urllib.request.build_opener(_NoRedirect)
    cur = url
    for _ in range(5):
        req = urllib.request.Request(cur, headers={"User-Agent": "filen-delta", "Range": "bytes=0-0"})
        try:
            with opener.open(req, timeout=30):
                return cur
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                cur = urllib.parse.urljoin(cur, e.headers["Location"])
                continue
            raise
    raise Fail("too many redirects")


class Remote:
    """Single-range reader with URL re-resolution and retry."""

    def __init__(self, page_url):
        self.page_url = page_url
        self.url = None
        self.requests = 0
        self.bytes = 0

    def _ensure(self, force=False):
        if self.url is None or force:
            log(f"  resolving release URL ...")
            self.url = resolve(self.page_url)

    def stream(self, start, end, sink, tries=5):
        """Fetch bytes [start, end) with ONE Range header, calling sink(bytes). Resumes on error."""
        pos = start
        attempt = 0
        while pos < end:
            try:
                self._ensure(force=attempt > 0)
                req = urllib.request.Request(self.url, headers={
                    "Range": f"bytes={pos}-{end - 1}", "User-Agent": "filen-delta"})
                self.requests += 1
                with urllib.request.urlopen(req, timeout=60) as r:
                    if r.status != 206:
                        raise Fail(f"expected 206, got {r.status} (server ignored Range)")
                    cr = r.headers.get("Content-Range", "")
                    if not cr.startswith(f"bytes {pos}-"):
                        raise Fail(f"unexpected Content-Range '{cr}' for start {pos}")
                    while pos < end:
                        b = r.read(min(CHUNK, end - pos))
                        if not b:
                            break
                        sink(b)
                        pos += len(b)
                        self.bytes += len(b)
                if pos < end:
                    raise urllib.error.URLError("short read")
            except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
                attempt += 1
                if attempt >= tries:
                    raise Fail(f"network failure at byte {pos}: {e}")
                log(f"  ! {e}; retry {attempt}/{tries - 1} from byte {pos} in {2 * attempt}s")
                time.sleep(2 * attempt)

    def read(self, start, n):
        buf = bytearray()
        self.stream(start, start + n, buf.extend)
        return bytes(buf)


# ---------------------------------------------------------------- rish seed

class Seed:
    def __init__(self, path, rish):
        self.path, self.rish = path, rish
        self.size = int(self._run(f"stat -c %s '{path}'").decode().strip())

    def _run(self, cmd):
        p = subprocess.run([self.rish, "-c", cmd], capture_output=True)
        if p.returncode != 0:
            raise Fail(f"rish failed ({cmd}): {p.stderr.decode(errors='replace').strip()}")
        return p.stdout

    def read(self, start, n):
        data = self._run(f"tail -c +{start + 1} '{self.path}' | head -c {n}")
        if len(data) != n:
            raise Fail(f"seed read short: wanted {n}, got {len(data)} at {start}")
        return data

    def stream(self, start, end, sink):
        cmd = f"tail -c +{start + 1} '{self.path}' | head -c {end - start}"
        p = subprocess.Popen([self.rish, "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        got = 0
        while True:
            b = p.stdout.read(CHUNK)
            if not b:
                break
            sink(b)
            got += len(b)
        p.wait()
        if got != end - start or p.returncode != 0:
            raise Fail(f"seed stream wrong: wanted {end - start}, got {got}, rc {p.returncode}")


# ---------------------------------------------------------------- zip parsing

def parse_zip(src, size):
    """Return (entries, cd_off, region_end). entries: name -> dict. Raises Fail on zip64."""
    n = min(size, 65535 + 22)
    tail = src.read(size - n, n)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise Fail("no zip end-of-central-directory record", 4)
    (_, _, _, nent, _, cd_size, cd_off, _) = struct.unpack("<IHHHHIIH", tail[i:i + 22])
    if cd_off == 0xFFFFFFFF or nent == 0xFFFF:
        raise Fail("zip64 not supported", 4)
    cd = src.read(cd_off, cd_size)
    ents, p = {}, 0
    for _ in range(nent):
        (sig, _, _, flags, method, _, _, crc, csize, usize, nl, el, cl, _, _, _, loff) = \
            struct.unpack("<IHHHHHHIIIHHHHHII", cd[p:p + 46])
        if sig != 0x02014B50:
            raise Fail("bad central directory entry", 4)
        name = cd[p + 46:p + 46 + nl]
        ents[name] = dict(flags=flags, method=method, crc=crc, csize=csize, usize=usize, off=loff)
        p += 46 + nl + el + cl
    # APK Signing Block sits between the last entry and the central directory.
    region_end = cd_off
    if cd_off >= 24:
        tl = src.read(cd_off - 24, 24)
        if tl[8:] == b"APK Sig Block 42":
            blk = struct.unpack("<Q", tl[:8])[0]
            region_end = cd_off - blk - 8
    # entry regions: [off, next off) ; last one ends at region_end
    offs = sorted(e["off"] for e in ents.values())
    nxt = {o: (offs[k + 1] if k + 1 < len(offs) else region_end) for k, o in enumerate(offs)}
    for e in ents.values():
        e["end"] = nxt[e["off"]]
    return ents, cd_off, region_end


def plan(new, seed, new_size, new_region_end):
    """Return ordered segments [(kind, start, end, seed_off)] covering [0, new_size)."""
    reuse = []
    for name, e in sorted(new.items(), key=lambda kv: kv[1]["off"]):
        s = seed.get(name)
        if (s and s["crc"] == e["crc"] and s["csize"] == e["csize"] and s["usize"] == e["usize"]
                and s["method"] == e["method"] and s["flags"] == e["flags"]
                and s["end"] - s["off"] == e["end"] - e["off"]):
            reuse.append((e["off"], e["end"], s["off"]))
    # coalesce contiguous in both files
    runs = []
    for a, b, c in reuse:
        if runs and runs[-1][1] == a and runs[-1][2] + (runs[-1][1] - runs[-1][0]) == c:
            runs[-1][1] = b
        else:
            runs.append([a, b, c])
    runs = [r for r in runs if r[1] - r[0] >= MIN_COPY]
    segs, pos = [], 0
    for a, b, c in runs:
        if a > pos:
            segs.append(("fetch", pos, a, None))
        segs.append(("copy", a, b, c))
        pos = b
    if pos < new_size:
        segs.append(("fetch", pos, new_size, None))
    return segs


# ---------------------------------------------------------------- main flow

def find_seed(rish):
    """Return the installed base.apk path, or None if the package is not installed.
    Raises Fail with rish's own exit code and stderr if rish itself fails."""
    cmd = f"pm path {PKG}"
    log(f"  running: {rish} -c '{cmd}'")
    try:
        p = subprocess.run([rish, "-c", cmd], capture_output=True)
    except OSError as e:
        raise Fail(f"cannot execute rish ('{rish}'): {e}. If rish is a fish function/alias, "
                   f"python cannot call it; pass --rish /path/to/rish")
    out = p.stdout.decode(errors="replace").strip()
    err = p.stderr.decode(errors="replace").strip()
    log(f"  rish exit={p.returncode} stdout={out[:200]!r} stderr={err[:300]!r}")
    if p.returncode != 0:
        raise Fail(f"rish failed (exit {p.returncode}): {err or out or 'no output'}. "
                   f"Check RISH_APPLICATION_ID is exported (set -gx) in this shell")
    lines = [l.strip()[8:] for l in out.splitlines() if l.strip().startswith("package:")]
    base = [l for l in lines if l.endswith("/base.apk")] or lines
    return base[0] if base else None


def mb(n):
    return f"{n / 1e6:.1f} MB"


def verify(path, size, sha):
    if os.path.getsize(path) != size:
        return False
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(CHUNK), b""):
            h.update(b)
    return h.hexdigest() == sha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--dir", required=True)
    ap.add_argument("--rish", default=shutil.which("rish") or "rish")
    ap.add_argument("--api", default="https://api.github.com")
    ap.add_argument("--dl", default="https://github.com")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--full", action="store_true", help="skip delta, full resumable download")
    a = ap.parse_args()

    os.makedirs(a.dir, exist_ok=True)
    final = os.path.join(a.dir, f"{a.tag}-{ASSET}")
    meta = final + ".sha256"
    part = final + ".part"

    # ---- 1. offline path: verified cached APK
    banner(1, 6, "Cached APK (offline path)")
    if os.path.exists(final) and os.path.exists(meta):
        sha, size = open(meta).read().split()[:2]
        if verify(final, int(size), sha):
            log(f"  cached and verified: {final} ({mb(int(size))}); no network needed")
            print(final)
            return 0
        log("  cached APK failed verification; ignoring it (not deleting)")
    else:
        log("  no verified cache; going online")

    # ---- 2. release metadata
    banner(2, 6, "Release metadata (REST)")
    rel = http_json(f"{a.api}/repos/{REPO}/releases/tags/{a.tag}")
    asset = next((x for x in rel["assets"] if x["name"] == ASSET), None)
    if not asset or not asset.get("digest", "").startswith("sha256:"):
        raise Fail("asset or sha256 digest missing in release", 3)
    size, sha = asset["size"], asset["digest"][7:]
    log(f"  {ASSET}: {size} bytes ({mb(size)}), sha256 {sha}")

    # ---- 3. preflight
    banner(3, 6, "Preflight")
    have = os.path.getsize(part) if os.path.exists(part) else 0
    free = shutil.disk_usage(a.dir).free
    need = size + MARGIN - have
    log(f"  free {mb(free)}; need ~{mb(need)} (APK + {mb(MARGIN)} margin); below 1 GiB")
    if free < need:
        raise Fail(f"not enough free space in {a.dir}", 2)

    page = f"{a.dl}/{REPO}/releases/download/{a.tag}/{ASSET}"
    remote = Remote(page)
    used_delta = False

    # ---- 4. delta plan
    segs = None
    if not a.full:
        banner(4, 6, "Delta plan (installed APK as seed)")
        try:
            sp = find_seed(a.rish)
            if not sp:
                raise Fail(f"rish ran fine but `pm path {PKG}` returned no package; using full download")
            seed = Seed(sp, a.rish)
            log(f"  seed: {sp} ({mb(seed.size)})")
            sents, _, _ = parse_zip(seed, seed.size)
            nents, _, new_end = parse_zip(remote, size)
            segs = plan(nents, sents, size, new_end)
            c = sum(e - s for k, s, e, _ in segs if k == "copy")
            f = size - c
            log(f"  copy from seed: {mb(c)} in {sum(k == 'copy' for k, *_ in segs)} segment(s)")
            log(f"  fetch over network: {mb(f)} in {sum(k == 'fetch' for k, *_ in segs)} range request(s)")
            if c == 0:
                log("  nothing reusable; delta pointless")
                segs = None
        except Fail as e:
            log(f"  delta unavailable: {e}")
            segs = None
    else:
        banner(4, 6, "Delta plan skipped (--full)")

    if a.dry_run:
        log("\n  --dry-run: stopping before any download")
        return 0

    # ---- 5. assemble or download
    banner(5, 6, "Assemble delta" if segs else "Full resumable download")
    if segs:
        h = hashlib.sha256()
        with open(part, "wb") as out:
            def sink(b):
                out.write(b)
                h.update(b)
            for k, s, e, c in segs:
                log(f"  {k:5s} {s}-{e} ({mb(e - s)})" + (f" <- seed@{c}" if k == "copy" else ""))
                if k == "copy":
                    seed.stream(c, c + (e - s), sink)
                else:
                    remote.stream(s, e, sink)
        used_delta = h.hexdigest() == sha and os.path.getsize(part) == size
        if not used_delta:
            log("  ! delta result failed sha256/size; discarding assembled file and falling back")
            os.remove(part)
            have = 0
    if not used_delta:
        have = os.path.getsize(part) if os.path.exists(part) else 0
        log(f"  downloading from byte {have}")
        with open(part, "ab") as out:
            remote.stream(have, size, out.write)

    # ---- 6. verify + publish
    banner(6, 6, "Verify")
    if not verify(part, size, sha):
        raise Fail(f"verification failed; leaving {part} for inspection", 4)
    os.replace(part, final)
    with open(meta, "w") as m:
        m.write(f"{sha} {size}\n")
    log(f"  OK: {final}")
    log(f"  network used: {mb(remote.bytes)} in {remote.requests} request(s) "
        f"({'delta' if used_delta else 'full'})")
    print(final)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Fail as e:
        log(f"\nERROR: {e}")
        sys.exit(e.code)
    except (urllib.error.URLError, OSError, ValueError) as e:
        log(f"\nERROR: {type(e).__name__}: {e}")
        sys.exit(3)
