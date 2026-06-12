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

# Run the Python scanner using `pipreqs`
cd $projectID
pipreqs . | tee ../generated/python-scanner.log
cd ..
if [ -f $projectID/requirements.txt ]
then 
    echo "Packages" > generated/python-deps.csv
    cat $projectID/requirements.txt >> generated/python-deps.csv
fi
if [ -f generated/python-deps.csv ]; then $pythonbin tools/csv2md.py generated/python-deps.csv; fi
