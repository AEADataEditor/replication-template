#!/bin/bash
# 26_update_jira_software.sh
# Detect software used (Stata, R, Python, etc.) from the program files listed
# by 04_list_program_files.sh, and add any newly-identified software to the
# Jira issue's "Software used" field (customfield_10028). Never removes
# existing values.
#
# Ticket resolved in order: $jiraticket env var -> config.yml -> openICPSR directory detection.
#
# Usage: 26_update_jira_software.sh <project-dir> [tag]
#   project-dir  Directory the deposit was unpacked into (used to inspect .ipynb kernel language).
#   tag          Optional. Matches the $tag suffix used by 04_list_program_files.sh, if any.

_project_dir="${1:-}"
_tag="${2:-}"

if command -v python3.12 &>/dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    echo "26_update_jira_software: no Python 3 found, skipping"
    exit 0
fi

_suffix=""
[ -z "$_tag" ] || _suffix=".$_tag"
_metadata="generated/programs-metadata${_suffix}.csv"

if [ ! -f "$_metadata" ]; then
    echo "26_update_jira_software: $_metadata not found, skipping"
    exit 0
fi

_jira="${jiraticket:-}"
echo "26_update_jira_software: jiraticket from environment: '${_jira}'"

if [ -z "$_jira" ]; then
    if [ -f config.yml ] && [ -f tools/parse_yaml.sh ]; then
        . ./tools/parse_yaml.sh
        _jira=$(parse_yaml config.yml | grep '^jiraticket=' | sed 's/jiraticket=//;s/"//g')
        echo "26_update_jira_software: jiraticket from config.yml: '${_jira}'"
    else
        echo "26_update_jira_software: config.yml or parse_yaml.sh not found, skipping config.yml lookup"
    fi
fi

if [ -z "$_jira" ]; then
    _icpsr=$(find . -maxdepth 1 -mindepth 1 -type d -name '[123][0-9][0-9][0-9][0-9][0-9]' 2>/dev/null \
             | head -1 | xargs -I{} basename {} 2>/dev/null || true)
    if [ -n "$_icpsr" ]; then
        echo "26_update_jira_software: detected openICPSR directory '${_icpsr}', looking up Jira ticket"
        _jira=$($PYTHON_CMD tools/jira_find_task_by_icpsr.py "$_icpsr" 2>&1) || true
        echo "26_update_jira_software: jiraticket from lookup: '${_jira}'"
    else
        echo "26_update_jira_software: no openICPSR directory found"
    fi
fi

if [ -z "$_jira" ]; then
    echo "26_update_jira_software: no Jira ticket found, skipping"
    exit 0
fi

$PYTHON_CMD tools/jira_update_software.py "$_jira" "$_metadata" --project-dir "$_project_dir" --yes || \
    echo "26_update_jira_software: Warning - failed to update Software used field"

exit 0
