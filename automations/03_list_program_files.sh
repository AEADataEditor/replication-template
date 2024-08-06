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

extensions="do r rmd ox m py ipynb sas jl f f90 c c++ sh"

[ -z $tag ] || tag=".$tag"
outfile=$(pwd)/generated/programs-list$tag.txt
out256=$(pwd)/generated/programs-list$tag.$(date +%Y-%m-%d).sha256
summary=$(pwd)/generated/programs-summary$tag.txt
metadata=$(pwd)/generated/programs-metadata$tag.csv


if [ ! -d $directory ]
then
  echo "$directory not a directory"
  exit 2
else
  cd $directory
  # initialize
  echo "Generated on $(date)" > "$outfile"
  echo "The deposit contains " > $summary
  echo "filename,lines" > $metadata

  # go over the list of extensions

  for ext in $extensions
  do
    find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)                          |sort >> "$outfile"
    find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)  -exec sha256sum "{}" \; |sort>> "$out256"
    count=$(grep -i \\.$ext "$outfile" | wc -l)
    [ $count == 0 ] ||   printf "%4s %3s files, "  $count $ext >> $summary
    # add the number of lines in each file
    find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \) -exec wc -l "{}" \; | awk '{print substr($0,index($0,$2)) "," $1}' |sort >> $metadata
  done

  # wrap up

  echo "of which [ONE, NONE] is a main/master file." >> $summary

fi
