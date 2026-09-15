#!/bin/bash
#set -ev


[[ "$SkipProcessing" == "yes" ]] && exit 0
[[ "$ProcessPython" == "no" ]] && exit 0

# Define the $pythonbin variable based on the operating system using a case statement
case "$(uname -o)" in
  Msys)
    pythonbin="python"
    ;;
  *)
    [[ -z $pythonbin ]] && pythonbin="python3"
    ;;
esac

if [ ! -d generated ] 
then 
  mkdir generated
fi

projectID=$1
if [ -f tools/requirements-scanner.txt ]; then $pythonbin -m pip install -r tools/requirements-scanner.txt; fi

# Run the Python scanner using `pipreqs`, writing the scan result to
# generated/requirements-generated.txt so replicators can use it directly
# (and so we never touch an author-provided requirements.txt).
cd $projectID
pipreqs . --savepath ../generated/requirements-generated.txt | tee ../generated/python-scanner.log
cd ..
# Reconcile the scan with any author-provided requirements.txt: filters out
# conda environment dumps, writes python-deps.csv and a software-warnings fragment
$pythonbin tools/filter_requirements.py \
    --author "$projectID/requirements.txt" \
    --scanned generated/requirements-generated.txt \
    --deps-csv generated/python-deps.csv \
    --warnings generated/software-warnings-python.md
if [ -f generated/python-deps.csv ]; then $pythonbin tools/csv2md.py generated/python-deps.csv; fi
