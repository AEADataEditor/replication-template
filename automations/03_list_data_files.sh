#!/bin/bash
#set -ev

if [ -z $1 ]
then
cat << EOF
$0 (directory) [(tag)] [(zipfile)]

where (directory) could be the openICPSR ID, Zenodo ID, etc., or a separate
directory containing files from outside the deposit (e.g., restricted data).
The optional zipfile parameter indicates the name of the zipfile that was extracted.

If generated/manifest(.tag).txt already exists (created by 02_create_manifest.sh),
this script filters it instead of re-walking the file tree.
EOF
exit 2
fi
directory=$1
tag=$2
zipfile=$3


if [ ! -d generated ]
then
  mkdir generated
fi

extensions="gpkg dat dta rda rds rdata ods xls xlsx mat csv  txt shp xml prj dbf sav pkl jld jld2 gz sas7bdat rar zip 7z tar tgz bz2 xz parquet pqt json jsonl  hdf5 hdf hdf4 netcdf"

# Include tag in filename if it exists
suffix=""
[ -z $tag ] || suffix="$suffix.$tag"

outfile=$(pwd)/generated/data-list$suffix.txt
out256=$(pwd)/generated/data-list$suffix.$(date +%Y-%m-%d).sha256
metadata=$(pwd)/generated/data-metadata$suffix.csv

manifest=$(pwd)/generated/manifest$suffix.txt
manifest_metadata=$(pwd)/generated/metadata$suffix.txt

# build a case-insensitive "ends with one of these extensions" regex, e.g. \.(dta|csv|...)(,[0-9]+)?$
ext_regex="\.($(echo $extensions | tr -s ' ' '|'))(,[0-9]+)?\$"

if [ ! -d $directory ]
then
  echo "$directory not a directory"
  exit 2
else
  cd $directory

  # Remove existing sha256 file if present
  if [ -f "$out256" ]; then
    rm "$out256"
  fi

  if [ -f "$manifest" ] && [ -f "$manifest_metadata" ]
  then
    # manifest already exists: filter it instead of re-scanning the file tree
    echo "Generated on $(date) (filtered from $(basename $manifest))" > "$outfile"
    echo "filename,bytes" > $metadata

    grep -v "^Generated on" "$manifest" | grep -Ei "$ext_regex" | sort >> "$outfile"
    grep -v "^filename,bytes" "$manifest_metadata" | grep -Ei "$ext_regex" | sort >> $metadata
  else
    # fall back to walking the file tree directly
    echo "Generated on $(date)" > "$outfile"
    echo "filename,bytes" > $metadata

    for ext in $extensions
    do
      find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)                          |sort  >> "$outfile"
      # get size of file
      find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \) -printf "%p,%s\n" |sort >> $metadata
    done
  fi
fi
