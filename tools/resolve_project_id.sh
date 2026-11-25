#!/bin/bash
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Lars Vilhuber and contributors.
# Author(s): Lars Vilhuber
# Licensed under the BSD 3-Clause License; see the LICENSE file at the repository root.

# Resolve the deposit identifiers and the deposit directory name (projectID).
#
# Source this file from the repository root; do not execute it:
#   . ./tools/resolve_project_id.sh
#
# Sets, with pipeline/environment variables taking precedence over config.yml:
#   openICPSRID  (config.yml: openicpsr)
#   WorldBankID  (config.yml: worldbank)
#   DataverseID  (config.yml: dataverse)
#   ZenodoID     (config.yml: zenodo)
#   OSFID        (config.yml: osf)
#   projectID    the deposit directory, from the first identifier that is set:
#                  openICPSR  -> <openICPSRID>
#                  World Bank -> wb-<DOI suffix or catalog ID>
#                  Dataverse  -> dv-<...>        (download_dv.py --dir-name)
#                  Zenodo     -> zenodo-<record> (download_zenodo.py --dir-name)
#                  OSF        -> osf-<project>   (download_osf.sh; not yet in the pipelines)
#                empty if no identifier is set.
# jiraticket: environment, else config.yml (tools/resolve_jiraticket.sh decides
# it once, in the Download step).
# If no identifier is set at all but jiraticket is, openICPSRID is read from the
# ticket's "openICPSR Project Number" (late ingest with empty fields); it stays
# empty when Jira has none, and the other downloaders then try the ticket.

. ./tools/parse_yaml.sh
_rpi_env_jiraticket="${jiraticket:-}"
eval $(parse_yaml config.yml)
jiraticket="${_rpi_env_jiraticket:-$jiraticket}"
unset _rpi_env_jiraticket

openICPSRID="${openICPSRID:-$openicpsr}"
WorldBankID="${WorldBankID:-$worldbank}"
DataverseID="${DataverseID:-$dataverse}"
ZenodoID="${ZenodoID:-$zenodo}"
OSFID="${OSFID:-$osf}"

if [ -z "$openICPSRID$WorldBankID$DataverseID$ZenodoID$OSFID" ] && [ -n "$jiraticket" ]; then
    openICPSRID=$(python3 tools/jira_get_info.py "$jiraticket" openicpsr 2>/dev/null || true)
    export openICPSRID
fi

projectID="$openICPSRID"
if [ -z "$projectID" ] && [ -n "$WorldBankID" ]; then
    _rpi_wbid="${WorldBankID%/}"
    projectID="wb-${_rpi_wbid##*/}"
    unset _rpi_wbid
fi
if [ -z "$projectID" ] && [ -n "$DataverseID" ]; then
    projectID=$(python3 tools/download_dv.py "$DataverseID" --dir-name)
fi
if [ -z "$projectID" ] && [ -n "$ZenodoID" ]; then
    projectID=$(python3 tools/download_zenodo.py --zenodo-id "$ZenodoID" --dir-name)
fi
if [ -z "$projectID" ] && [ -n "$OSFID" ]; then
    _rpi_osf="${OSFID%/}"
    projectID="osf-${_rpi_osf##*/}"
    unset _rpi_osf
fi

echo "Project ID: ${projectID:-(none)}"
