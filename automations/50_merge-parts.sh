#!/bin/bash
# This simply combines Parts A and B of the report

# read functions

report=REPLICATION.md
parta=REPLICATION-PartA.md
partb=REPLICATION-PartB.md

if [ ! -z $jiraticket ] 
then 
  premsg="$jiraticket #comment [skip ci] "
else
  premsg="[skip ci] "
fi


# start the process

# Verify that all files are there

if [[ ! -f $parta ]]
then
  echo "ERROR: $parta not found"
  exit 1
fi

if [[ ! -f $partb ]]
then
  echo "ERROR: $partb not found"
  exit 1
fi

# signal the overwriting

if [[ -f $report ]]
then
  echo "============================================================"
  echo "WARNING: $report will be overwritten."
  echo "============================================================"
fi


# combine the parts 

cat $parta  $partb > $report

# remove the parts

git rm $parta
git rm $partb
git add -v $report

git commit -m "${premsg}Merged report"


