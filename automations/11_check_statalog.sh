#!/bin/bash
set -ev

[[ "$SkipProcessing" == "yes" ]] && exit 0

if [ ! -z $1 ] 
then 
    folder=$1
    # find logfile
    logdate=$(date +%-d_%b_%Y)
    logfile="$(find $folder -name logfile_\*${logdate}\*-root.log | sort | tail -1)"


    EXIT_CODE=0
    if [[ -f "$logfile" ]]
    then

        echo "===== $logfile ====="
        cat "$logfile"

        # Fail CI if Stata ran with an error
        LOG_CODE=$(tail -1 "$logfile" | tr -d '[:cntrl:]')
        echo "===== LOG CODE: $LOG_CODE ====="
        [[ ${LOG_CODE:0:1} == "r" ]] && EXIT_CODE=1 
    else
        echo "$logfile not found"
        EXIT_CODE=2
    fi
    echo "==== Exiting with code $EXIT_CODE"
    #exit $EXIT_CODE
    exit 0
fi
