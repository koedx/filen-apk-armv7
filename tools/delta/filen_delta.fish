# filen_delta.fish - delta-install a Filen armv7 release APK (see spec/delta-installer.md)
# Usage: filen_delta TAG [--dry-run] [--no-install] [--full]
# Layout: clone koedx/filen-apk-armv7 to ~/dev/filen/filen-apk-armv7; filen_delta.py lives next to this file in tools/delta.
# Override the script dir with FILEN_DELTA_HOME. APKs are cached OUTSIDE the repo in ~/dev/filen/apks
# (override with FILEN_DELTA_APKS); this tool never deletes them.

function filen_delta --description 'Delta-install a Filen armv7 release APK'
    argparse 'dry-run' 'no-install' 'full' -- $argv; or return 2
    if test (count $argv) -ne 1
        echo 'usage: filen_delta TAG [--dry-run] [--no-install] [--full]'
        return 2
    end

    set -l tag $argv[1]
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

    # Python logs to stderr (shown live); stdout is only the final APK path.
    set -l apk (python3 -I $home/filen_delta.py $tag --dir $apkdir $pyargs)
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
    echo
    set_color --bold; echo "===== install ====="; set_color normal
    set_color red; echo "Install $apk ($bytes bytes) over $pkg with pm install -r?"; set_color normal
    read -P "[y/N] " -l ans
    if not string match -qi y $ans
        echo "skipped; APK kept at $apk"
        return 0
    end

    echo "streaming: cat $apk | rish -c 'pm install -r -S $bytes'"
    cat $apk | rish -c "pm install -r -S $bytes"
    set -l irc $pipestatus[2]
    if test $irc -ne 0
        set_color red; echo "pm install failed (exit $irc); APK kept at $apk"; set_color normal
        return $irc
    end

    echo
    set_color --bold; echo "===== installed package ====="; set_color normal
    rish -c "pm path $pkg; dumpsys package $pkg | grep -E 'versionName|primaryCpuAbi|lastUpdateTime'"
end
