#!/bin/bash
#set -ev

# Re-runs the data and program file listing scripts (03, 04) whenever
# generated/manifest(.tag).txt has changed relative to what is committed,
# so downstream lists stay in sync with a manually edited or refreshed manifest.

[[ "$SkipProcessing" == "yes" ]] && exit 0

if [ -z $1 ]
then
cat << EOF
$0 (directory) [(tag)] [(zipfile)]

where (directory) could be the openICPSR ID, Zenodo ID, etc., or a separate
directory containing files from outside the deposit (e.g., restricted data).
The optional zipfile parameter indicates the name of the zipfile that was extracted.
EOF
exit 2
fi
directory=$1
tag=$2
zipfile=$3

suffix=""
[ -z $tag ] || suffix="$suffix.$tag"

manifest=generated/manifest$suffix.txt

if [ ! -f "$manifest" ]
then
  echo "$manifest not found; run 02_create_manifest.sh first. Nothing to do."
  exit 0
fi

if [ -z "$(git status --porcelain -- "$manifest" 2>/dev/null)" ]
then
  echo "$manifest unchanged since last commit; skipping re-list"
  exit 0
fi

echo "$manifest changed; re-running data and program file listings"
./automations/03_list_data_files.sh "$directory" "$tag" "$zipfile"
./automations/04_list_program_files.sh "$directory" "$tag" "$zipfile"
