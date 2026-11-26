# filen_delta.fish - delta-install a Filen armv7 release APK (see docs/delta-installer.md)
# Needs: python3, adb (pkg install android-tools) connected to the tablet itself (adb connect localhost:5555).
# Usage: filen_delta TAG|--latest [--dry-run] [--no-install] [--full]   (--latest needs network: it asks GitHub for the newest release)
# Layout: clone koedx/filen-apk-armv7 to ~/dev/filen/filen-apk-armv7; filen_delta.py lives next to this file in tools/delta.
# Override the script dir with FILEN_DELTA_HOME. APKs are cached OUTSIDE the repo in ~/dev/filen/apks
# (override with FILEN_DELTA_APKS); this tool never deletes them.

function filen_delta --description 'Delta-install a Filen armv7 release APK'
    argparse 'dry-run' 'no-install' 'full' 'latest' -- $argv; or return 2
    set -l want 1
    set -q _flag_latest; and set want 0
    if test (count $argv) -ne $want
        echo 'usage: filen_delta TAG|--latest [--dry-run] [--no-install] [--full]'
        return 2
    end

    set -l tag latest
    test $want -eq 1; and set tag $argv[1]
    set -l home (set -q FILEN_DELTA_HOME; and echo $FILEN_DELTA_HOME; or echo ~/dev/filen/filen-apk-armv7/tools/delta)
    set -l apkdir (set -q FILEN_DELTA_APKS; and echo $FILEN_DELTA_APKS; or echo ~/dev/filen/apks)
    set -l pkg io.filen.app
    set -l pyargs

    set_color --bold; echo "===== filen_delta: $tag (UTC "(date -u +%Y-%m-%dT%H:%M:%SZ)") ====="; set_color normal
    echo "script: $home/filen_delta.py"
    echo "cache : $apkdir"
    test -f $home/filen_delta.py; or begin
        set_color red; echo "missing $home/filen_delta.py"; set_color normal
        return 2
    end

    set -q _flag_dry_run; and set -a pyargs --dry-run
    set -q _flag_full; and set -a pyargs --full
    set -q _flag_latest; and set -a pyargs --latest

    # adb device: prefer ...:5555, else the sole online device (the loopback adbd often shows as emulator-5554)
    set -l serial (adb devices 2>/dev/null | string match -r -g '^(\S+:5555)\s+device' | head -n1)
    test -z "$serial"; and set serial (adb devices 2>/dev/null | string match -r -g '^(\S+)\s+device\b' | head -n1)
    test -n "$serial"; and set -a pyargs --serial $serial

    # Python logs to stderr (shown live); stdout is only the final APK path.
    set -l tagarg
    test $want -eq 1; and set tagarg $tag
    set -l apk (python3 -I $home/filen_delta.py $tagarg --dir $apkdir $pyargs)
    set -l rc $status
    if test $rc -ne 0
        set_color red; echo "filen_delta.py failed (exit $rc); nothing installed"; set_color normal
        return $rc
    end
    if set -q _flag_dry_run
        echo "dry run complete"
        return 0
    end
    if set -q _flag_no_install
        echo "APK ready (not installed): $apk"
        return 0
    end

    set -l bytes (stat -c %s $apk)
    # re-detect: the python step may have run `adb connect`
    set serial (adb devices 2>/dev/null | string match -r -g '^(\S+:5555)\s+device' | head -n1)
    test -z "$serial"; and set serial (adb devices 2>/dev/null | string match -r -g '^(\S+)\s+device\b' | head -n1)
    echo
    set_color --bold; echo "===== install ====="; set_color normal
    if test -z "$serial"
        set_color red; echo "no online adb device; APK kept at $apk (run: adb connect localhost:5555)"; set_color normal
        return 1
    end
    set_color red; echo "Install $apk ($bytes bytes) over $pkg with adb -s $serial install -r?"; set_color normal
    read -P "[y/N] " -l ans
    if not string match -qi y $ans
        echo "skipped; APK kept at $apk"
        return 0
    end

    echo "running: adb -s $serial install -r $apk"
    adb -s $serial install -r $apk
    set -l irc $status
    if test $irc -ne 0
        set_color red; echo "adb install failed (exit $irc); APK kept at $apk"; set_color normal
        return $irc
    end

    echo
    set_color --bold; echo "===== installed package ====="; set_color normal
    adb -s $serial shell "pm path $pkg; dumpsys package $pkg | grep -E 'versionName|primaryCpuAbi|lastUpdateTime'"
end
