#!/bin/bash
#set -ev
#
# Usage: 00_unpack_zip.sh [--keep-zip] [project]
#
# Unpacks <project>.zip into <project>/, then deletes <project>.zip to free
# disk space (Bitbucket stops steps that run out of it). Pass --keep-zip when
# the ZIP is still needed afterwards (e.g. it is moved into cache/ as an
# artifact for later steps). ZIP files inside <project>/ are part of the
# deposit and are never deleted.

keep_zip=no
args=()
for arg in "$@"
do
  case "$arg" in
    --keep-zip) keep_zip=yes ;;
    *) args+=("$arg") ;;
  esac
done
set -- "${args[@]}"


# read parameters (sets projectID from config.yml)
. ./tools/resolve_project_id.sh

project="$projectID"

echo "Active project: $project (parsed from config.yml)"
# override per command line
if [[ ! -z $1 ]]
then
  project=$1
  echo "Active project: $project (parsed/override from command line)"
fi


if [[ -z $project ]]
then
  echo "No project found"
  exit 1
fi

zipfile=$project.zip

if [[ -f $zipfile ]]
then
  basename=$(basename $zipfile .zip)
  echo "Unzipping $zipfile to $basename"
  if unzip -n $zipfile -d $basename
  then
    if [[ "$keep_zip" == "yes" ]]
    then
      echo "Keeping $zipfile (--keep-zip)"
    else
      echo "Removing $zipfile to free disk space"
      rm -f $zipfile
    fi
  else
    echo "Unzipping $zipfile failed - keeping it"
  fi
fi

# Check if the project directory exists and has up to 5 ZIP files
if [[ -d $project ]]
then
  # Count the number of ZIP files in the project directory
  zip_count=$(find $project -maxdepth 1 -type f  -iname "*.zip"  | wc -l)
  
  if [[ $zip_count -le 5 && $zip_count -gt 0 ]]
  then
    # Find all ZIP files
    zipfiles=$(find $project -maxdepth 1 -type f  -iname "*.zip" )
    
    zipfile_suffixes=""
    
    # Process each ZIP file
    while IFS= read -r zipfile; do
      # Extract the filename without path and extension
      inner_zipname=$(basename "$zipfile" .zip)
      echo "Found ZIP file: $zipfile"
      
      # Unzip the file 
      unzip -n "$zipfile" -d "$project"
      
      # Collect zipfile names for export
      if [[ -z "$zipfile_suffixes" ]]; then
        zipfile_suffixes="$inner_zipname"
      else
        zipfile_suffixes="$zipfile_suffixes,$inner_zipname"
      fi
      
      echo "Unzipped ZIP file to $project"
    done <<< "$zipfiles"
    
    # Export the zipfile names for use in subsequent scripts
    echo "export ZIPFILE_SUFFIX=\"$zipfile_suffixes\"" > "$project/.zipfile_info"
    echo "Set ZIPFILE_SUFFIX=$zipfile_suffixes for subsequent scripts"
  fi
fi