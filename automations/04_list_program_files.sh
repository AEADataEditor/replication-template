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

extensions="ado do r rmd qmd ox m py nb ipynb sas jl f f90 c c++ sh toml yaml yml toml fs fsx gss cpp h"
# these usually do not have extensions
fullnames="makefile"

# Include tag in filename if it exists
suffix=""
[ -z $tag ] || suffix="$suffix.$tag"

outfile=$(pwd)/generated/programs-list$suffix.txt
out256=$(pwd)/generated/programs-list$suffix.$(date +%Y-%m-%d).sha256
summary=$(pwd)/generated/programs-summary$suffix.txt
metadata=$(pwd)/generated/programs-metadata$suffix.csv

manifest=$(pwd)/generated/manifest$suffix.txt

# case-insensitive "ends with one of these extensions" regex
ext_regex="\.($(echo $extensions | tr -s ' ' '|'))\$"
# case-insensitive "basename is one of these fullnames" regex
name_regex="(^|/)($(echo $fullnames | tr -s ' ' '|'))\$"


if [ ! -d $directory ]
then
  echo "$directory not a directory"
  exit 2
else
  cd $directory
  # initialize
  echo "The deposit contains " > $summary
  echo "filename,lines" > $metadata

  # Remove existing sha256 file if present
  if [ -f "$out256" ]; then
    rm "$out256"
  fi

  if [ -f "$manifest" ]
  then
    # manifest already exists: filter it instead of re-scanning the file tree
    echo "Generated on $(date) (filtered from $(basename $manifest))" > "$outfile"

    grep -v "^Generated on" "$manifest" | grep -Ei "$ext_regex|$name_regex" | sort >> "$outfile"

    for ext in $extensions
    do
      count=$(grep -i \\.$ext "$outfile" | wc -l)
      [ $count == 0 ] ||   printf "%4s %3s files, "  $count $ext >> $summary
    done

    for filename in $fullnames
    do
      count=$(grep -i \\$filename "$outfile" | wc -l)
      [ $count == 0 ] ||   printf "%4s %3s files, "  $count $filename >> $summary
    done

    # add the number of lines in each file
    while IFS= read -r f
    do
      [ -f "$f" ] && wc -l "$f"
    done < <(grep -v "^Generated on" "$outfile") | awk '{print substr($0,index($0,$2)) "," $1}' | sort >> $metadata
  else
    # fall back to walking the file tree directly
    echo "Generated on $(date)" > "$outfile"

    # go over the list of extensions

    for ext in $extensions
    do
      find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)                          |sort >> "$outfile"
      count=$(grep -i \\.$ext "$outfile" | wc -l)
      [ $count == 0 ] ||   printf "%4s %3s files, "  $count $ext >> $summary
      # add the number of lines in each file
      find . -type f \( -iname "*.$ext" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \) -exec wc -l "{}" \; | awk '{print substr($0,index($0,$2)) "," $1}' |sort >> $metadata
    done

    for filename in $fullnames
    do
      find . -type f \( -iname "$filename" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \)                          |sort >> "$outfile"
      count=$(grep -i \\$filename "$outfile" | wc -l)
      [ $count == 0 ] ||   printf "%4s %3s files, "  $count $ext >> $summary
      # add the number of lines in each file
      find . -type f \( -iname "$filename" ! -path "*/__MACOSX/*" ! -path "*./__MACOSX/*" \) -exec wc -l "{}" \; | awk '{print substr($0,index($0,$2)) "," $1}' |sort >> $metadata
    done
  fi

  # wrap up

  echo "of which [ONE, NONE] is a main/master file." >> $summary

fi
