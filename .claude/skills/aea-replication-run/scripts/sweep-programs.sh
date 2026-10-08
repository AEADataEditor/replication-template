#!/bin/bash
# Run each program of a replication package in its own Stata container.
#
# Why one container per program: a single failure doesn't stop the sweep, so one
# pass yields the complete failure inventory instead of one bug per full run.
# Safe when each program starts with `clear all` and its own `use` — verify that
# before relying on it, and follow up with a sequential run to catch any
# cross-file ordering dependency this cannot see.
#
# Usage:
#   sweep-programs.sh <deposit-dir> <filelist> <outdir> [stata-wrapper]
#
#   <deposit-dir>  directory containing config.do; also what gets mounted
#   <filelist>     one program path per line, relative to <deposit-dir>
#   <outdir>       where per-program logs and summary.tsv are written
#   [stata-wrapper] defaults to stata19
#
# Build the filelist from your master file so the order matches, e.g.:
#   grep -oP '(?<=^do ")\$\{rootdir\}/\K[^"]+' master.do > filelist.txt
#
# Prerequisite: chmod -R go+w <deposit-dir>. The container runs as gid 100
# (users); if your host user shares that gid, `o+w` alone leaves it unwritable
# and every run dies before executing a line.

set -u

DEPOSIT="${1:?need deposit dir}"
FILELIST="${2:?need file list}"
OUTDIR="${3:?need output dir}"
STATA="${4:-stata19}"

cd "$DEPOSIT" || exit 1
mkdir -p "$OUTDIR"
SUMMARY="$OUTDIR/summary.tsv"
: > "$SUMMARY"

i=0
while IFS= read -r f; do
    [ -z "$f" ] && continue
    i=$((i + 1))
    tag=$(printf "%03d" "$i")

    # Sentinel echoed at the end is how we detect success. The wrapper's exit
    # code always reflects its trailing system-info scripts, never Stata.
    cat > _iso.do <<EOF
include "config.do"
global data "\${rootdir}/data"
global outp "\${rootdir}/output"
cap mkdir "\${outp}"
cd "\${outp}"
do "\${rootdir}/${f}"
di as result "ISOLATE_SWEEP_OK"
cap log close ldi
EOF
    chmod go+w _iso.do
    rm -f _iso.log

    start=$(date +%s)
    # </dev/null is REQUIRED: `script` reads stdin and would otherwise consume
    # the remainder of FILELIST, silently ending the loop after one iteration.
    script -qec "$STATA -b do _iso.do" /dev/null >/dev/null 2>&1 </dev/null
    elapsed=$(( $(date +%s) - start ))

    log="$OUTDIR/${tag}.log"
    if [ -f _iso.log ]; then mv -f _iso.log "$log"; else echo "(no log produced)" > "$log"; fi

    if grep -q "ISOLATE_SWEEP_OK" "$log"; then
        status=PASS; err=""
    else
        status=FAIL
        err=$(grep -oE "^r\([0-9]+\);" "$log" | head -1)
        # No return code and no sentinel usually means the container was killed
        # (OOM), which is a machine property, not a defect in the code.
        [ -z "$err" ] && err="no-rc(killed/truncated?)"
    fi

    printf '%s\t%s\t%s\t%ss\t%s\n' "$tag" "$status" "$err" "$elapsed" "$f" >> "$SUMMARY"
    printf '%s %-4s %-22s %6ss  %s\n' "$tag" "$status" "$err" "$elapsed" "$f"
done < "$FILELIST"

rm -f _iso.do
echo "=== SWEEP COMPLETE ==="
printf 'PASS: %s  FAIL: %s\n' \
  "$(awk -F'\t' '$2=="PASS"' "$SUMMARY" | wc -l)" \
  "$(awk -F'\t' '$2=="FAIL"' "$SUMMARY" | wc -l)"
echo "Failures:"
awk -F'\t' '$2=="FAIL"{printf "  %s  %s\n", $3, $5}' "$SUMMARY"
