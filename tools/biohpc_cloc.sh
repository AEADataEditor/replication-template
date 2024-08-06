#!/bin/bash

if [[ -z $1 ]]
then
    echo "Usage: $0 <project_dir>"
    exit 1
fi

docker=$(which docker1)
[ -z $docker ] && docker=$(which docker)
if [[ -z $docker ]]
then
    echo "Docker not found"
    exit 1
fi



clocimg=aldanial/cloc
docker=docker1
$docker run --rm -v $(pwd):/tmp \
   --entrypoint=/bin/bash $clocimg  \
   ./automations/05_count_lines.sh $1

