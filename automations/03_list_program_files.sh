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

extensions="do r rmd ox m py ipynb sas jl f f90 c c++ sh"
outfile=$(pwd)/generated/programs-list.txt
[ -z $tag ] || outfile=$(pwd)/generated/programs-list.${tag}.txt
out256=$(pwd)/generated/programs-list.$(date +%Y-%m-%d).sha256
summary=$(pwd)/generated/programs-summary.txt
[ -z $tag ] || summary=$(pwd)/generated/programs-summary.${tag}.txt


if [ ! -d $projectID ]
then
  echo "$projectID not a directory"
  exit 2
else
  cd $projectID
  # initialize
  echo "Generated on $(date)" > "$outfile"
  echo "The deposit contains " > $summary

  # go over the list of extensions

  for ext in $extensions
  do
    find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)                          |sort >> "$outfile"
    find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)  -exec sha256sum "{}" \; |sort>> "$out256"
    count=$(grep -i \\.$ext "$outfile" | wc -l)
    [ $count == 0 ] ||   printf "%4s %3s files, "  $count $ext >> $summary
  done

  # wrap up

  echo "of which [ONE, NONE] is a main/master file." >> $summary

fi
