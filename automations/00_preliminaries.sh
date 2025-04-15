#!/bin/bash

if [ "$1" == "no" ]; then exit 0; fi

# Define the $pythonbin variable based on the operating system using a case statement
case "$(uname -o)" in
  Msys)
    pythonbin="python"
    ;;
  *)
    pythonbin="python3"
    ;;
esac

projectID=$2

if [ -d cache ]; then ls -lR cache/*; fi
if [ -f cache/$projectID.zip ]; then mv cache/$projectID.zip .; fi
if [ ! -f $projectID.zip ]; then $pythonbin tools/download_openicpsr-private.py $projectID; fi
./automations/00_unpack_zip.sh  $projectID
