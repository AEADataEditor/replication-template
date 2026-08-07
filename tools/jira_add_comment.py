#!/usr/bin/env python3
"""
Post a comment to a Jira issue.

Usage:
    python3 jira_add_comment.py <issue-key> <comment>

Arguments:
    issue-key   Jira issue key (e.g., AEAREP-8885 or aearep-8885)
    comment     Comment text (Jira wiki markup supported)

Output:
    Prints confirmation to stdout on success
    Prints warning to stderr on failure (non-fatal; always exits 0)

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


def add_comment(issue_key, comment):
    """Post a comment to the given Jira issue."""
    jira = get_jira_client()
    if not jira:
        print("Warning: Jira credentials not available, skipping comment", file=sys.stderr)
        return

    issue_key = issue_key.upper()
    try:
        jira.add_comment(issue_key, comment)
        print(f"Jira comment posted to {issue_key}")
    except Exception as e:
        print(f"Warning: Could not post Jira comment to {issue_key}: {e}", file=sys.stderr)


def main():
    if len(sys.argv) < 3 or sys.argv[1] in ['-h', '--help']:
        print("Usage: jira_add_comment.py <issue-key> <comment>", file=sys.stderr)
        print("Environment: JIRA_USERNAME, JIRA_API_KEY", file=sys.stderr)
        sys.exit(1 if len(sys.argv) < 3 else 0)

    issue_key = sys.argv[1]
    comment = sys.argv[2]
    add_comment(issue_key, comment)


if __name__ == '__main__':
    main()
