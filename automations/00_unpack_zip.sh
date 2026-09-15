#!/bin/bash
#set -ev


. ./tools/parse_yaml.sh

# read parameters
eval $(parse_yaml config.yml)

project="${openicpsr:-$dataverse}"
project="${project:-$zenodo}"
project="${project:-$osf}"

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
  unzip -n $zipfile -d $basename
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