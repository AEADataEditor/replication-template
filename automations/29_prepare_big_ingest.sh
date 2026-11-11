#!/bin/bash
# 29_prepare_big_ingest.sh
# Called when the regular ingest pipeline aborts because the deposit is too big
# for its cache. Prepares the hand-over to the big ingest pipeline:
#   1. If the deposit (generated/deposit-size.csv) needs more disk than a 2x worker
#      has free (bigingest_threshold_mb and bigingest_margin_mb in config.yml),
#      switch the big pipeline to a 4x VM in bitbucket-pipelines.yml, then commit
#      and push that change.
#   2. Post a Jira comment saying the regular pipeline aborted because the deposit
#      is too big, and the big pipeline is being triggered.
# The trigger itself (atlassian/trigger-pipeline) is a pipe in the YAML.
#
# Usage: 29_prepare_big_ingest.sh <regular-pipeline-name> <big-pipeline-name>

regular="$1"
big="$2"
if [ -z "$regular" ] || [ -z "$big" ]; then
    echo "Usage: $0 <regular-pipeline-name> <big-pipeline-name>" >&2
    exit 2
fi

msg="Deposit is too big for the regular pipeline; triggering ${big}."
python3 tools/big_ingest.py needs-4x
rc=$?
if [ $rc -eq 0 ]; then
    msg="${msg} Using a 4x VM."
    if python3 tools/big_ingest.py set-vm-size bitbucket-pipelines.yml "$big" 4x; then
        ./automations/20_commit_code.sh bitbucket-pipelines.yml notag
        git push || exit 1
    fi
elif [ $rc -ne 1 ]; then
    exit $rc
fi

./automations/70_publish_comment.sh "$regular" aborted "$msg"
exit 0
