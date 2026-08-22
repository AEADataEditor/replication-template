#!/bin/bash
# 26_update_jira_software.sh
# Detect software used (Stata, R, Python, etc.) from the program files listed
# by 04_list_program_files.sh, and add any newly-identified software to the
# Jira issue's "Software used" checkbox field (Stata/MATLAB/R/Python/SAS/Julia),
# falling back to the "Software used (other)" text field for anything that
# isn't one of those checkbox options. Never removes existing values.
#
# Ticket resolved in order: $jiraticket env var -> config.yml -> openICPSR directory detection.
#
# Usage: 26_update_jira_software.sh <project-dir> [tag]
#   project-dir  Directory the deposit was unpacked into (used to inspect .ipynb kernel language).
#   tag          Optional. Matches the $tag suffix used by 04_list_program_files.sh, if any.
#
# Stdout carries only the "Software detected: ..." line (if any software was
# found), so a caller can capture it and forward it to 70_publish_comment.sh
# as a durable fallback for cases where the "Software used" field write fails
# (e.g. one of the fields missing from an issue's screen). All other
# diagnostics go to stderr.
#
# Exit code propagates tools/jira_update_software.py's status (0 success,
# 1 on failure to update Jira); append `|| true` at the call site if the
# pipeline should continue regardless.

_project_dir="${1:-}"
_tag="${2:-}"

if command -v python3.12 &>/dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    echo "26_update_jira_software: no Python 3 found, skipping" >&2
    exit 0
fi

_suffix=""
[ -z "$_tag" ] || _suffix=".$_tag"
_metadata="generated/programs-metadata${_suffix}.csv"

if [ ! -f "$_metadata" ]; then
    echo "26_update_jira_software: $_metadata not found, skipping" >&2
    exit 0
fi

_jira="${jiraticket:-}"
echo "26_update_jira_software: jiraticket from environment: '${_jira}'" >&2

if [ -z "$_jira" ]; then
    if [ -f config.yml ] && [ -f tools/parse_yaml.sh ]; then
        . ./tools/parse_yaml.sh
        _jira=$(parse_yaml config.yml | grep '^jiraticket=' | sed 's/jiraticket=//;s/"//g')
        echo "26_update_jira_software: jiraticket from config.yml: '${_jira}'" >&2
    else
        echo "26_update_jira_software: config.yml or parse_yaml.sh not found, skipping config.yml lookup" >&2
    fi
fi

if [ -z "$_jira" ]; then
    _icpsr=$(find . -maxdepth 1 -mindepth 1 -type d -name '[123][0-9][0-9][0-9][0-9][0-9]' 2>/dev/null \
             | head -1 | xargs -I{} basename {} 2>/dev/null || true)
    if [ -n "$_icpsr" ]; then
        echo "26_update_jira_software: detected openICPSR directory '${_icpsr}', looking up Jira ticket" >&2
        _jira=$($PYTHON_CMD tools/jira_find_task_by_icpsr.py "$_icpsr" 2>&1) || true
        echo "26_update_jira_software: jiraticket from lookup: '${_jira}'" >&2
    else
        echo "26_update_jira_software: no openICPSR directory found" >&2
    fi
fi

if [ -z "$_jira" ]; then
    echo "26_update_jira_software: no Jira ticket found, skipping" >&2
    exit 0
fi

_output=$($PYTHON_CMD tools/jira_update_software.py "$_jira" "$_metadata" --project-dir "$_project_dir" --yes 2>&1)
_rc=$?
echo "$_output" >&2
[ $_rc -eq 0 ] || echo "26_update_jira_software: Warning - failed to update Software used field" >&2

_sw_line=$(echo "$_output" | grep '^Software detected:')
if [ -n "$_sw_line" ] && [ "$_sw_line" != "Software detected: (none)" ]; then
    echo "$_sw_line"
fi

exit $_rc
