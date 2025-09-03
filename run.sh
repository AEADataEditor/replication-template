#!/bin/bash
#set -ev

# Get some functions

. ./tools/parse_yaml.sh

# read parameters
eval $(parse_yaml config.yml)

project="${openicpsr:-$dataverse}"
project="${project:-$zenodo}"
project="${project:-$osf}"

main="${main:-main.do}"

statabin="${statabin:-stata-mp}"
rbin="${rbin:-R}"

maindir="$(dirname "$main")"

if [[ "$maindir" == "." ]]
then
  # we don't have a path
  fullmain="$(find $project -name $main)"
  maindir="$(dirname "$fullmain")"
fi

ext=$(echo $main | awk -F. ' { print $2 } ')

echo "Active project: $project"
echo "Configured main file: $main"
echo "Configured subdir: $maindir"
echo "Identified extension: $ext"

# go into the project directory
set -ev

# show all the files
find $project -type f

# now go to where the main file is
cd "$maindir"


case $ext in
   do)
     if [[ -z $(which $statabin 2>/dev/null || echo "" ) ]]
     then
       echo "Stata not found - skipping"
       exit 0
     fi
     $statabin -b do "$main"
     ;;
   R|r)
     if [[ -z $(which $rbin 2>/dev/null || echo "" ) ]]
     then
       echo "R not found - skipping"
       exit 0
     fi
      $rbin CMD BATCH "$main"
     ;;
esac
