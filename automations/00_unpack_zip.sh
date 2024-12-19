#!/bin/bash
set -ev


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