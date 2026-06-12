#!/usr/bin/env python3
"""
Find highest-numbered Jira Task for a given openICPSR project ID.

Usage:
    python3 jira_find_task_by_icpsr.py <openICPSR-ID>

Arguments:
    openICPSR-ID    openICPSR project number (e.g., 123456)

Output:
    Prints the highest-numbered Jira Task issue key to stdout (e.g., AEAREP-8885)
    Prints nothing if not found or credentials missing
    Exit code 0 on success, 1 on usage error

Environment Variables Required:
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens
"""

import os
import sys
from jira import JIRA


def get_jira_client():
    """Initialize and return authenticated Jira client."""
    jira_username = os.environ.get('JIRA_USERNAME')
    jira_api_key = os.environ.get('JIRA_API_KEY')

    if not jira_username or not jira_api_key:
        return None

    try:
        return JIRA(
            server="https://aeadataeditors.atlassian.net",
            basic_auth=(jira_username, jira_api_key),
            options={'verify': True}
        )
    except Exception:
        return None


def find_task_by_icpsr(openicpsr_id):
    """
    Find the highest-numbered Jira Task issue for the given openICPSR project ID.

    Returns:
        Issue key string (e.g., 'AEAREP-8885'), or empty string if not found.
    """
    jira = get_jira_client()
    if not jira:
        return ""

    try:
        all_fields = jira.fields()
        field_map = {f['name']: f['id'] for f in all_fields}
        field_id = field_map.get('openICPSR Project Number')

        if field_id:
            # Use cf[XXXXX] syntax for reliable custom field JQL queries
            cf_number = field_id.replace('customfield_', '')
            jql = (
                f'project = AEAREP AND issuetype = Task '
                f'AND cf[{cf_number}] = "{openicpsr_id}" '
                f'ORDER BY key DESC'
            )
        else:
            # Fallback: use display name in quotes
            jql = (
                f'project = AEAREP AND issuetype = Task '
                f'AND "openICPSR Project Number" = "{openicpsr_id}" '
                f'ORDER BY key DESC'
            )

        issues = jira.search_issues(jql, maxResults=1)
        if issues:
            return issues[0].key
    except Exception:
        pass

    return ""


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print("Usage: jira_find_task_by_icpsr.py <openICPSR-ID>", file=sys.stderr)
        print("Environment: JIRA_USERNAME, JIRA_API_KEY", file=sys.stderr)
        sys.exit(1 if len(sys.argv) < 2 else 0)

    openicpsr_id = sys.argv[1].strip()
    result = find_task_by_icpsr(openicpsr_id)
    if result:
        print(result)


if __name__ == '__main__':
    main()
