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

[ -z $tag ] || tag=".$tag" 
outfile=$(pwd)/generated/manifest$tag.txt
out256=$(pwd)/generated/manifest$tag.$(date +%Y-%m-%d).sha256
metadata=$(pwd)/generated/metadata$tag.txt

if [ ! -d $directory ]
then
  echo "$directory not a directory"
  exit 2
else
  cd $directory
  # initialize
  echo "Generated on $(date)" > "$outfile"
  echo "filename,bytes" > $metadata

  # Remove existing sha256 file if present
  if [ -f "$out256" ]; then
    rm "$out256"
  fi

  # Do checksums for all files

  find . -type f \(  ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)                          |sort >> "$outfile"
  find . -type f \(  ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)  -exec sha256sum "{}" \; |sort -k 2 >> "$out256"
  # get size of file
  find . -type f \(  ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \) -printf "%p,%s\n"        |sort >> $metadata
fi
