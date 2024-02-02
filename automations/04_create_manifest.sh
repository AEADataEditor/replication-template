#!/bin/bash
set -ev

if [ -z $1 ]
then
cat << EOF
$0 (projectID) [(tag)]

where (projectID) could be openICPSR, Zenodo, etc. ID.
EOF
exit 2
fi
projectID=$1
tag=$2

if [ ! -d generated ] 
then 
  mkdir generated
fi

outfile=$(pwd)/generated/manifest.txt
[ -z $tag ] || outfile=$(pwd)/generated/manifest.${tag}.txt
out256=$(pwd)/generated/manifest.$(date +%Y-%m-%d).sha256

if [ ! -d $projectID ]
then
  echo "$projectID not a directory"
  exit 2
else
  cd $projectID
  # initialize
  echo "Generated on $(date)" > "$outfile"

  # Do checksums for all files

  find . -type f \(  ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)                          |sort >> "$outfile"
  find . -type f \(  ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)  -exec sha256sum "{}" \; |sort >> "$out256"
fi