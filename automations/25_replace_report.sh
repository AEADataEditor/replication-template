#!/bin/bash
#set -ev

report=REPLICATION.md
parta=REPLICATION-PartA.md
partb=REPLICATION-PartB.md


[[ "$SkipProcessing" == "yes" ]] && exit 0

if [ ! -z $jiraticket ] 
then 
  premsg="$jiraticket #comment [skip ci] "
else
  premsg="[skip ci] "
fi

# check the  checksum of the REPLICATION.md that created earlier

if [[ ! -f generated/REPLICATION.sha256 ]] 
then
    echo "No previous checksum"
    exit 0
fi

if [ -f generated/REPLICATION-filled.md ]
then
    echo "Verifying checksum against blank report"
    sha256sum -c generated/REPLICATION.sha256 || exit 0
    case $? in
    0)
    echo "Replacing $report"
    mv generated/REPLICATION-filled.md $report
    git add -v $report
    git commit -m "${premsg}Updated report" $report
    # splitting the report - NEW in 2024
    splitline=$(grep -n "You are starting \*PartB\*." $report | cut -f1 -d:)
    head -n $(( splitline - 1))  $report > $parta
    tail -n +$splitline          $report > $partb
    git add -v $parta $partb
    git commit -m "${premsg}Added split report" $parta $partb
    exit 0
    ;;
    *)
    echo "Original $report has already been edited. Not splitting"
    echo "Verify generated/REPLICATION-filled.md"
    mv generated/REPLICATION-filled.md $report
    git add -v $report
    git commit -m "${premsg}Updated report" $report
    exit 0
    ;;
    esac
fi
