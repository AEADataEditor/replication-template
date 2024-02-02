#!/bin/bash

python=python3

# may need a fallback to generic python
#

# Assumes:
# pip install zenodo_get

if [[ -z $1 ]]
then
  cat << EOF
  $0 (projectID)

  will download a Zenodo archive
EOF
exit 2
fi
projectID=$1
if [ ${#projectID} -gt 7 ]
then
	projectID=${projectID##*.}
fi

# Test if directory exists
#

zenodo_dir=zenodo-$projectID

if [ -d $zenodo_dir ]
then
	echo "$zenodo_dir already exists - please remove prior to downloading"
	exit 2
fi
zenodo_get --output-dir=$zenodo_dir $projectID
