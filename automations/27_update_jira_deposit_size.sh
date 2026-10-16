#!/bin/bash
# 27_update_jira_deposit_size.sh
# Compute the size of the just-downloaded deposit and record it (in MB) on
# the Jira issue's "Deposit size" field. Always overwrites the field, since
# ingest pipelines can run multiple times.
#
# Ticket resolved in order: $jiraticket env var -> config.yml -> openICPSR directory detection.
#
# Usage: 27_update_jira_deposit_size.sh <project-dir>
#   project-dir  Directory the deposit was unpacked into (e.g. $projectID).
#
# Must run before the envelope ZIP (if any) is moved out of the current
# directory (e.g. before "mv *.zip cache/"), so tools/jira_update_deposit_size.py
# can still see it.
#
# Exit code propagates tools/jira_update_deposit_size.py's status (0 success,
# 1 on failure to update Jira); append `|| true` at the call site if the
# pipeline should continue regardless.

_project_dir="${1:-}"

if command -v python3.12 &>/dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    echo "27_update_jira_deposit_size: no Python 3 found, skipping" >&2
    exit 0
fi

if [ -z "$_project_dir" ] || [ ! -d "$_project_dir" ]; then
    echo "27_update_jira_deposit_size: project directory '$_project_dir' not found, skipping" >&2
    exit 0
fi

_jira="${jiraticket:-}"
echo "27_update_jira_deposit_size: jiraticket from environment: '${_jira}'" >&2

if [ -z "$_jira" ]; then
    if [ -f config.yml ] && [ -f tools/parse_yaml.sh ]; then
        . ./tools/parse_yaml.sh
        _jira=$(parse_yaml config.yml | grep '^jiraticket=' | sed 's/jiraticket=//;s/"//g')
        echo "27_update_jira_deposit_size: jiraticket from config.yml: '${_jira}'" >&2
    else
        echo "27_update_jira_deposit_size: config.yml or parse_yaml.sh not found, skipping config.yml lookup" >&2
    fi
fi

if [ -z "$_jira" ]; then
    _icpsr=$(find . -maxdepth 1 -mindepth 1 -type d -name '[123][0-9][0-9][0-9][0-9][0-9]' 2>/dev/null \
             | head -1 | xargs -I{} basename {} 2>/dev/null || true)
    if [ -n "$_icpsr" ]; then
        echo "27_update_jira_deposit_size: detected openICPSR directory '${_icpsr}', looking up Jira ticket" >&2
        _jira=$($PYTHON_CMD tools/jira_find_task_by_icpsr.py "$_icpsr" 2>&1) || true
        echo "27_update_jira_deposit_size: jiraticket from lookup: '${_jira}'" >&2
    else
        echo "27_update_jira_deposit_size: no openICPSR directory found" >&2
    fi
fi

if [ -z "$_jira" ]; then
    echo "27_update_jira_deposit_size: no Jira ticket found, skipping" >&2
    exit 0
fi

_output=$($PYTHON_CMD tools/jira_update_deposit_size.py "$_jira" "$_project_dir" --yes 2>&1)
_rc=$?
echo "$_output" >&2
[ $_rc -eq 0 ] || echo "27_update_jira_deposit_size: Warning - failed to update Deposit size field" >&2

exit $_rc
