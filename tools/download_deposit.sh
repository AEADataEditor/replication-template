#!/bin/bash
# Download the deposit from World Bank, Dataverse or Zenodo, when no openICPSR
# ID is set, and set projectID to the resulting directory.
#
# Source this file from the repository root, after tools/resolve_project_id.sh
# and after the openICPSR download; do not execute it:
#   . ./tools/download_deposit.sh
#
# Each downloader is tried in turn while projectID is empty. It is given the
# ID if one is set, else the Jira ticket (--jira-ticket); exit code 2 means
# "nothing for this repository" and is not an error.
#
# Sets:
#   wb_dir / dv_dir / zenodo_dir   directory created by that downloader (else unset)
#   projectID                      that directory
#   WorldBankID / DataverseID / ZenodoID   exported; filled in from the directory
#                                  or Jira when they were not given, and written
#                                  to config.yml by tools/update_config.sh

if [ -z "$projectID" ] && { [ -n "$WorldBankID" ] || [ -n "$jiraticket" ]; }; then
    wb_dir=$(python3 tools/download_worldbank.py ${WorldBankID:+"$WorldBankID"} ${jiraticket:+--jira-ticket "$jiraticket"} --print-id) || [ $? -eq 2 ]
fi
if [ -n "${wb_dir:-}" ]; then
    projectID="$wb_dir"
    export WorldBankID="${WorldBankID:-${wb_dir#wb-}}"
    ./tools/update_config.sh
fi

if [ -z "$projectID" ] && { [ -n "$DataverseID" ] || [ -n "$jiraticket" ]; }; then
    dv_dir=$(python3 tools/download_dv.py ${DataverseID:+"$DataverseID"} ${jiraticket:+--jira-ticket "$jiraticket"} --print-id) || [ $? -eq 2 ]
fi
if [ -n "${dv_dir:-}" ]; then
    projectID="$dv_dir"
    export DataverseID="${DataverseID:-$(python3 tools/jira_get_info.py "$jiraticket" replicationurl)}"
    ./tools/update_config.sh
fi

if [ -z "$projectID" ] && { [ -n "$ZenodoID" ] || [ -n "$jiraticket" ]; }; then
    zenodo_dir=$(python3 tools/download_zenodo.py ${ZenodoID:+--zenodo-id "$ZenodoID"} ${jiraticket:+--jira-ticket "$jiraticket"} --print-id) || [ $? -eq 2 ]
fi
if [ -n "${zenodo_dir:-}" ]; then
    projectID="$zenodo_dir"
    export ZenodoID="${zenodo_dir#zenodo-}"
    ./tools/update_config.sh
fi
