#!/bin/bash
# This simply combines Parts A and B of the report

# read functions arguments and define defaults

# If argument is "-h" print help and exit
if [[ "$1" == "-h" ]]
then
  echo "Usage: $0 [no arguments]"
  echo "This script combines Parts A and B of the report, and commits the result."
  echo "Possible optional arguments:"
    echo "  -h  print this help message"
    echo "Otherwise, positional arguments are read. First is the input report,"
    echo "second is part A, third is part B."
  exit 0
fi

# If there are arguments, read them
if [[ $# -gt 0 ]]
then
  report=$1
  basename=${report%.md}
  parta=${2:-${basename}-PartA.md}
  partb=${3:-${basename}-PartB.md}
else
    report=REPLICATION.md
    basename=${report%.md}
    parta=${basename}-PartA.md
    partb=${basename}-PartB.md
fi

# start the process

# Verify that all files are there

if [[ ! -f $report ]]
then
  echo "ERROR: $report not found"
  exit 1
fi

if [[ -f $parta ]]
then
  echo "WARNING: $parta will be overwritten"
fi

if [[ -f $partb ]]
then
  echo "WARNING: $partb will be overwritten"
fi



    # splitting the report - NEW in 2024
    splitline=$(grep -n "You are starting \*PartB\*." $report | cut -f1 -d:)
    if [[ -z $splitline ]]
    then
        echo "ERROR: Split line not found in $report - aborting"
        exit 1
    fi
    head -n $(( splitline - 1))  $report > $parta
    tail -n +$splitline          $report > $partb
    git add $parta $partb
    git commit -m '[skipci] Added split report' $parta $partb


