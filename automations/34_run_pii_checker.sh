#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

# 34_run_pii_checker.sh
# Check the deposit's data files for PII with pii-checker
# (https://github.com/AEADataEditor/pii-checker) and a local Ollama model.
# Run by the p-pii-checker pipeline on the self-hosted runner that serves Ollama.
#
# The deposit is downloaded into a scratch directory outside the repository,
# so nothing in the checkout changes except the files written to generated/.
# (The checked-out <project>/ holds only the code the ingest committed, and
# may have been edited by the replicator: it is not used.) pii-checker
# unpacks archives in the deposit itself. tools/run_pii_checker.py writes:
#   pii-checker-full/pii_checker_results.xlsx     values observed in the data; an
#                                                 artifact of the pipeline run, never committed
#   generated/pii_checker_results-nodetails.xlsx  without the values; committed
#   generated/pii_checker_summary.txt             counts, for the Jira comment; or, if
#                                                 the model stays too slow (exit 3), why
#                                                 the check did not run
#
# Usage: 34_run_pii_checker.sh (project)
#
# Environment:
#   openICPSRID, WorldBankID, DataverseID, ZenodoID
#                    from tools/resolve_project_id.sh (config.yml, or the
#                    environment, which takes precedence); the first one set
#                    picks the downloader
#   PiiModel         Ollama model (default: gemma4:26b)
#   PiiCheckerRef    branch or tag of pii-checker (default: main)
#   PiiMinTokensPerSec  slowest acceptable speed of the loaded model, in tokens/s;
#                    0 skips the check (default: tools/run_pii_checker.py's)
#   PiiWaitMinutes   how long to keep reloading the model to reach that speed (default: 30)
#   PiiRetryMinutes  pause between reloads (default: 5)
#   OLLAMA_ENDPOINTS Ollama URL (default: the step container's gateway, port 11434)

if [ -z "$1" ]
then
  echo "Usage: $0 (project)"
  exit 2
fi
project=$1
tools="$PWD/tools"
# the deposit identifiers: sourced here, since the caller's are not exported
. ./tools/resolve_project_id.sh

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# --- the deposit, into $work/$project ---
(
  cd "$work" || exit 1
  if [ -n "$openICPSRID" ]; then python3 "$tools/download_openicpsr-private.py" "$openICPSRID"
  elif [ -n "$WorldBankID" ]; then python3 "$tools/download_worldbank.py" "$WorldBankID"
  elif [ -n "$DataverseID" ]; then python3 "$tools/download_dv.py" "$DataverseID"
  elif [ -n "$ZenodoID" ]; then python3 "$tools/download_zenodo.py" --zenodo-id "$ZenodoID"
  else echo "34_run_pii_checker: no deposit identifier in config.yml or the pipeline variables"; exit 2
  fi
  rm -f ./*.zip   # the downloaded archive, once extracted
) || exit 2
if [ ! -d "$work/$project" ]
then
  echo "34_run_pii_checker: download did not produce $project"
  exit 2
fi

# --- pii-checker, in an environment of its own (its pins can differ from requirements.txt) ---
git clone --quiet --depth 1 --branch "${PiiCheckerRef:-main}" \
    https://github.com/AEADataEditor/pii-checker.git "$work/pii-checker" || exit 1
python3 -m venv "$work/venv" || exit 1
"$work/venv/bin/pip" install --quiet -r "$work/pii-checker/requirements.txt" || exit 1

[ -d generated ] || mkdir generated
rm -f generated/pii_checker_summary.txt   # a previous run's, which a failure must not post
"$work/venv/bin/python" tools/run_pii_checker.py "$work/$project" \
    --checker-dir "$work/pii-checker" --model "${PiiModel:-gemma4:26b}" \
    ${PiiMinTokensPerSec:+--min-tokens-per-sec "$PiiMinTokensPerSec"} \
    --wait-minutes "${PiiWaitMinutes:-30}" --retry-minutes "${PiiRetryMinutes:-5}" \
    --summary-file generated/pii_checker_summary.txt
