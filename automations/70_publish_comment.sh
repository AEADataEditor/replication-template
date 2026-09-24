#!/bin/bash
# 70_publish_comment.sh
# Post a status comment to the Jira issue associated with this repository,
# or (with --config) post a comment describing uncommitted config.yml changes.
# Ticket resolved in order: $jiraticket env var → config.yml → openICPSR directory detection.
#
# Usage:
#   70_publish_comment.sh [pipeline-name] [status] [extra-message]
#   70_publish_comment.sh --config [pipeline-name] [extra-message]
#
#   pipeline-name  Optional. Name of the Bitbucket custom pipeline (e.g., "1-populate-from-icpsr").
#                  No Bitbucket built-in variable exposes this; pass it explicitly from the pipeline.
#   status         Optional. Status of the pipeline: "started" or "completed" (default: "completed").
#   extra-message  Optional. Appended to the comment as-is, e.g. the
#                  "Software detected: ..." line captured from
#                  26_update_jira_software.sh's stdout (status mode), or a
#                  reminder tied to what changed (--config mode).
#   --config       Post a comment with the current uncommitted `git diff -- config.yml`
#                  instead of a status message. No-ops if there is no diff. Useful
#                  after any pipeline step that may have modified config.yml.

_config_mode=""
if [ "$1" = "--config" ]; then
    _config_mode="true"
    shift
fi

_pipeline="${1:-}"

# Detect Python command
if command -v python3.12 &>/dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    echo "70_publish_comment: no Python 3 found, skipping Jira notification"
    exit 0
fi

_jira="${jiraticket:-}"
echo "70_publish_comment: jiraticket from environment: '${_jira}'"

# Fall back to config.yml
if [ -z "$_jira" ]; then
    if [ -f config.yml ] && [ -f tools/parse_yaml.sh ]; then
        . ./tools/parse_yaml.sh
        _jira=$(parse_yaml config.yml | grep '^jiraticket=' | sed 's/jiraticket=//;s/"//g')
        echo "70_publish_comment: jiraticket from config.yml: '${_jira}'"
    else
        echo "70_publish_comment: config.yml or parse_yaml.sh not found, skipping config.yml lookup"
    fi
fi

# Fall back to directory-based lookup
if [ -z "$_jira" ]; then
    _icpsr=$(find . -maxdepth 1 -mindepth 1 -type d -name '[123][0-9][0-9][0-9][0-9][0-9]' 2>/dev/null \
             | head -1 | xargs -I{} basename {} 2>/dev/null || true)
    if [ -n "$_icpsr" ]; then
        echo "70_publish_comment: detected openICPSR directory '${_icpsr}', looking up Jira ticket"
        _jira=$($PYTHON_CMD tools/jira_find_task_by_icpsr.py "$_icpsr" 2>&1) || true
        echo "70_publish_comment: jiraticket from lookup: '${_jira}'"
    else
        echo "70_publish_comment: no openICPSR directory found"
    fi
fi

if [ -z "$_jira" ]; then
    echo "70_publish_comment: no Jira ticket found, skipping comment"
    exit 0
fi

if [ -n "$_config_mode" ]; then
    _extra_message="${2:-}"
    _diff=$(git diff -- config.yml)
    if [ -z "$_diff" ]; then
        echo "70_publish_comment: no uncommitted config.yml changes, skipping comment"
        exit 0
    fi
    if [ -n "$_pipeline" ]; then
        _comment="config.yml updated by ${_pipeline}:
{code}${_diff}{code}"
    else
        _comment="config.yml updated:
{code}${_diff}{code}"
    fi
    if [ -n "$_extra_message" ]; then
        _comment="${_comment}

${_extra_message}"
    fi
    echo "70_publish_comment: posting config.yml diff comment to ${_jira}"
    $PYTHON_CMD tools/jira_add_comment.py "$_jira" "$_comment" || true
    exit 0
fi

_status="${2:-completed}"
_extra="${3:-}"

case "$_status" in
    started)
        _emoji="🚀"
        _verb="started"
        ;;
    completed)
        _emoji="✅"
        _verb="completed"
        ;;
    *)
        _emoji="ℹ️"
        _verb="$_status"
        ;;
esac

_url="https://bitbucket.org/$BITBUCKET_WORKSPACE/$BITBUCKET_REPO_SLUG/pipelines/results/$BITBUCKET_BUILD_NUMBER"
echo "70_publish_comment: posting ${_verb} comment to ${_jira}"
_comment="${_emoji} Bitbucket Pipeline ${_pipeline} ${_verb}. Build [#$BITBUCKET_BUILD_NUMBER|$_url]."
[ -z "$_extra" ] || _comment="${_comment} ${_extra}"
$PYTHON_CMD tools/jira_add_comment.py "$_jira" "$_comment" || true

exit 0
