#!/bin/bash
set -ev


[[ "$SkipProcessing" == "yes" ]] && exit 0
[[ "$ProcessPython" == "no" ]] && exit 0

if [ ! -d generated ] 
then 
  mkdir generated
fi

projectID=$1
if [ -f tools/requirements-scanner.txt ]; then pip install -r tools/requirements-scanner.txt; fi

# Run the Python scanner using `pipreqs`
cd $projectID
pipreqs . | tee ../generated/python-scanner.log
cd ..
if [ -f $projectID/requirements.txt ]
then 
    echo "Packages" > generated/python-deps.csv
    cat $projectID/requirements.txt >> generated/python-deps.csv
fi
if [ -f generated/python-deps.csv ]; then python3 tools/csv2md.py generated/python-deps.csv; fi

