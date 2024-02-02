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

extensions="dat dta rda rds ods xls xlsx mat csv rdata txt shp xml prj dbf sav pkl gz"
[ -z $tag ] && outfile=$(pwd)/generated/data-list.txt
[ -z $tag ] || outfile=$(pwd)/generated/data-list.${tag}.txt
out256=$(pwd)/generated/data-list.$(date +%Y-%m-%d).sha256

if [ ! -d $projectID ]
then
  echo "$projectID not a directory"
  exit 2
else
  cd $projectID
  # initialize
  echo "Generated on $(date)" > "$outfile"

  # go over the list of extensions

  for ext in $extensions
  do
    find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)                          |sort  >> "$outfile"
    find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)  -exec sha256sum "{}" \; | sort >> "$out256"
  done
fi
