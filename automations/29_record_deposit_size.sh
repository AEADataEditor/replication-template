#!/bin/bash
# 29_record_deposit_size.sh
# Record the ZIP size and unzipped size of the deposit in generated/deposit-size.csv.
# Used by the "Check downloads" step to decide whether the big ingest needs a
# larger VM; committed with the other generated/ files at the end.
#
# Usage: 29_record_deposit_size.sh <project-dir>

if [ -z "$1" ]; then
    echo "Usage: $0 <project-dir>" >&2
    exit 2
fi

mkdir -p generated
python3 tools/big_ingest.py record-size "$1"
