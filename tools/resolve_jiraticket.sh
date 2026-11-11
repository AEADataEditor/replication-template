#!/bin/bash
# Resolve the Jira ticket for this run, once, in the Download step.
#
# Source this file from the repository root, before anything evals config.yml
# (which would overwrite the pipeline's jiraticket variable); do not execute it:
#   . ./tools/resolve_jiraticket.sh
#
# Sets and exports jiraticket from the first source that has a value:
#   1. the jiraticket pipeline/environment variable (explicit override)
#   2. the newest Jira ticket for the openICPSR ID (tools/jira_find_task_by_icpsr.py)
#   3. jiraticket in config.yml
#   4. the Bitbucket repository name (aearep-NNNN -> AEAREP-NNNN)
# A revision reuses the repository and the openICPSR ID but gets a new ticket,
# so a value cached in config.yml is older than the lookup by design.
# Without Jira credentials or a match, the lookup yields nothing and the
# later sources apply.

. ./tools/parse_yaml.sh
_rjt_env_ticket="${jiraticket:-}"
_rjt_env_icpsr="${openICPSRID:-}"
if [ -f config.yml ]; then
    eval $(parse_yaml config.yml)
fi
_rjt_config_ticket="${jiraticket:-}"
_rjt_icpsr="${_rjt_env_icpsr:-${openicpsr:-}}"

jiraticket=""
_rjt_source=""
if [ -n "$_rjt_env_ticket" ]; then
    jiraticket="$_rjt_env_ticket"
    _rjt_source="the jiraticket pipeline variable"
else
    if [ -n "$_rjt_icpsr" ]; then
        jiraticket=$(python3 tools/jira_find_task_by_icpsr.py "$_rjt_icpsr" 2>/dev/null || true)
        _rjt_source="the newest ticket for openICPSR ID $_rjt_icpsr"
    fi
    if [ -z "$jiraticket" ] && [ -n "$_rjt_config_ticket" ]; then
        jiraticket="$_rjt_config_ticket"
        _rjt_source="config.yml"
    fi
    if [ -z "$jiraticket" ] && [[ "${BITBUCKET_REPO_SLUG:-}" =~ ^aearep-([0-9]+) ]]; then
        jiraticket="AEAREP-${BASH_REMATCH[1]}"
        _rjt_source="the repository name"
    fi
fi
export jiraticket

echo "Jira ticket: ${jiraticket:-(none)}${jiraticket:+ (from $_rjt_source)}"
unset _rjt_env_ticket _rjt_env_icpsr _rjt_config_ticket _rjt_icpsr _rjt_source
