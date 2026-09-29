#!/bin/bash
#set -ev

# Get some functions

. ./tools/parse_yaml.sh

# read parameters
eval $(parse_yaml config.yml)

projectID="${openicpsr}"
projectID="${projectID:-$dataverse}"
projectID="${projectID:-$zenodo}"
projectID="${projectID:-$osf}"

# Check if MainFile is provided from Bitbucket pipeline variable
# If provided, update config.yml and use it
if [ ! -z "$MainFile" ]; then
  echo "MainFile variable detected from pipeline: $MainFile"
  # Update config.yml with the new MainFile
  sed -i "s|^main:.*|main: $MainFile|" config.yml
  main="$MainFile"
  echo "Updated config.yml with main: $main"
else
  # Fall back to reading from config.yml
  main="${main:-main.do}"
fi

statabin="${statabin:-stata-mp}"
rbin="${rbin:-R}"

maindir="$(dirname "$main")"

if [[ "$maindir" == "." ]]
then
  # we don't have a path
  fullmain="$(find $projectID -name $main)"
  maindir="$(dirname "$fullmain")"
fi

ext=$(echo $main | awk -F. ' { print $2 } ')

echo "======================================================================"
echo "Active project: $projectID"
echo "Configured main file: $main"
echo "Configured subdir: $maindir"
echo "Identified extension: $ext"
echo "======================================================================"

# go into the project directory
set -ev

# show all the files
find $projectID -type f

# now go to where the main file is
echo "======================================================================"
echo "Changing directory to: $maindir"
cd "$maindir"


case $ext in
   do)
     if [[ -z $(which $statabin 2>/dev/null || echo "" ) ]]
     then
       echo "Stata not found - skipping"
       exit 0
     fi
     $statabin -b do "$main"
     [[ -f ${main%.do}.log ]] && tail -n 20 ${main%.do}.log || echo "No log file found."
     ;;
   R|r)
     if [[ -z $(which $rbin 2>/dev/null || echo "" ) ]]
     then
       echo "R not found - skipping"
       exit 0
     fi
      $rbin CMD BATCH "$main"
      [[ -f ${main%.R}.Rout ]] && tail -n 20 ${main%.R}.Rout || echo "No Rout file found."
     ;;
esac
