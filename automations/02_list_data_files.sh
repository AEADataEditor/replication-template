#!/bin/bash
set -ev

if [ -z $1 ]
then
cat << EOF
$0 (directory) [(tag)]

where (directory) could be the openICPSR ID, Zenodo ID, etc., or a separate
directory containing files from outside the deposit (e.g., restricted data).
EOF
exit 2
fi
directory=$1
tag=$2

if [ ! -d generated ] 
then 
  mkdir generated
fi

extensions="gpkg dat dta rda rds rdata ods xls xlsx mat csv  txt shp xml prj dbf sav pkl jld jld2 gz sas7bdat rar zip 7z tar tgz bz2 xz "

[ -z $tag ] || tag=".$tag"
outfile=$(pwd)/generated/data-list$tag.txt
out256=$(pwd)/generated/data-list$tag.$(date +%Y-%m-%d).sha256
metadata=$(pwd)/generated/data-metadata$tag.csv

if [ ! -d $directory ]
then
  echo "$directory not a directory"
  exit 2
else
  cd $directory
  # initialize
  echo "Generated on $(date)" > "$outfile"
  echo "filename,bytes" > $metadata

  # go over the list of extensions

  for ext in $extensions
  do
    find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)                          |sort  >> "$outfile"
    # get checksum
    find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)  -exec sha256sum "{}" \; | sort >> "$out256"
    # get size of file
    find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \) -printf "%p,%s\n" |sort >> $metadata
  done
fi
