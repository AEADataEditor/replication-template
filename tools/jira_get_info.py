#!/usr/bin/env python3
"""
JIRA Information Fetcher for AEA Data Editor

Retrieves various information fields from JIRA for a given issue.

Usage:
    python3 jira_get_info.py <issue-key> [keyword]
    python3 jira_get_info.py -h|--help

Arguments:
    issue-key    JIRA issue key (e.g., aearep-8361, AEAREP-1234)
    keyword      Type of information to retrieve (optional, defaults to 'doi')

Keywords:
    doi          - DOI (from RepositoryDOI or constructed from openICPSR fields)
    openicpsrurl - openICPSR alternate URL
    dcaf_private - Check if DCAF_Access_Restrictions_V2 contains "Yes, data can be made available privately"
                   Returns "yes" if present, empty string otherwise
    mcid         - Manuscript Central Identifier
    mctitle      - Manuscript title (extracted from Description field)
    sivacorid    - SIVACOR ID

Examples:
    python3 jira_get_info.py aearep-8361 doi
    python3 jira_get_info.py aearep-8361 openicpsrurl
    python3 jira_get_info.py aearep-8361 dcaf_private
    python3 jira_get_info.py aearep-8361 mcid
    python3 jira_get_info.py aearep-8361 mctitle
    python3 jira_get_info.py aearep-8361 sivacorid
    python3 jira_get_info.py aearep-8361              # defaults to 'doi'

Environment Variables Required:
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens

    To obtain a JIRA API token:
    1. Visit https://id.atlassian.com/manage-profile/security/api-tokens
    2. Click "Create API token"
    3. Copy the token and set it as JIRA_API_KEY environment variable

Output:
    Prints requested information to stdout
    Prints nothing if information is not available
    Exit code 0 on success, 1 on error

Error Handling:
    - Missing credentials: Exits silently with empty output
    - Invalid issue key: Exits silently with empty output
    - Unknown keyword: Prints error to stderr and exits with code 1
    - Network errors: Exits silently with empty output
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

    jira_url = "https://aeadataeditors.atlassian.net"

    try:
        jira = JIRA(
            server=jira_url,
            basic_auth=(jira_username, jira_api_key),
            options={'verify': True}
        )
        return jira
    except Exception:
        return None


def build_field_map(jira):
    """Build a mapping of field names to field IDs."""
    field_map = {}
    try:
        all_fields = jira.fields()
        for field in all_fields:
            field_map[field['name']] = field['id']
    except Exception:
        pass
    return field_map


def get_field_value(issue, field_map, field_name):
    """Get the value of a field by name."""
    field_id = field_map.get(field_name)
    if not field_id:
        return None

    try:
        return getattr(issue.fields, field_id, None)
    except Exception:
        return None


def get_doi_from_jira(issue, field_map):
    """
    Get DOI from JIRA issue.

    Returns:
        DOI string if found, empty string otherwise
    """
    # Try to get RepositoryDOI first
    repo_doi = get_field_value(issue, field_map, 'RepositoryDOI')

    if repo_doi and str(repo_doi).strip():
        return str(repo_doi).strip()

    # Fall back to constructing from openICPSR fields
    icpsr_number = get_field_value(issue, field_map, 'openICPSR Project Number')
    icpsr_version = get_field_value(issue, field_map, 'openICPSRversion')

    if icpsr_number and str(icpsr_number).strip():
        icpsr_num_str = str(icpsr_number).strip()
        icpsr_ver_str = str(icpsr_version).strip() if icpsr_version and str(icpsr_version).strip() else 'V1'
        return f'https://doi.org/10.3886/E{icpsr_num_str}{icpsr_ver_str}'

    return ""


def get_openicpsr_url_from_jira(issue, field_map):
    """
    Get openICPSR alternate URL from JIRA issue.

    Returns:
        openICPSR URL if found, empty string otherwise
    """
    url = get_field_value(issue, field_map, 'openICPSR alternate URL')

    if url and str(url).strip():
        return str(url).strip()

    return ""


def check_dcaf_private_data(issue, field_map):
    """
    Check if DCAF_Access_Restrictions_V2 contains "Yes, data can be made available privately".

    Returns:
        "yes" if the field contains the target text, empty string otherwise
    """
    dcaf_value = get_field_value(issue, field_map, 'DCAF_Access_Restrictions_V2')

    if dcaf_value:
        # Handle both string and list cases
        if isinstance(dcaf_value, list):
            # Check if any item in the list matches
            for item in dcaf_value:
                if "Yes, data can be made available privately" in str(item):
                    return "yes"
        elif "Yes, data can be made available privately" in str(dcaf_value):
            return "yes"

    return ""


def get_manuscript_central_id(issue, field_map):
    """
    Get Manuscript Central Identifier from JIRA issue.

    Returns:
        Manuscript Central Identifier if found, empty string otherwise
    """
    mcid = get_field_value(issue, field_map, 'Manuscript Central identifier')

    if mcid and str(mcid).strip():
        return str(mcid).strip()

    return ""


def get_manuscript_title(issue, field_map):
    """
    Get Manuscript title from JIRA issue Description field.
    Parses the description for text in quotes following "entitled".

    Returns:
        Manuscript title if found, empty string otherwise
    """
    import re

    # Get the description field
    description = issue.fields.description if hasattr(issue.fields, 'description') else None

    if not description:
        return ""

    # Look for pattern like 'entitled "Title Text"' in the first few lines
    lines = description.split('\n')[:10]  # Check first 10 lines

    for line in lines:
        # Match pattern: entitled "title" or entitled 'title'
        match = re.search(r'entitled\s+["\']([^"\']+)["\']', line, re.IGNORECASE)
        if match:
            # Remove trailing comma if present
            title = match.group(1).strip()
            return title.rstrip(',')

    return ""


def get_sivacor_id(issue, field_map):
    """
    Get SIVACOR ID from JIRA issue.

    Returns:
        SIVACOR ID if found, empty string otherwise
    """
    sivacor_id = get_field_value(issue, field_map, 'SIVACOR ID')

    if sivacor_id and str(sivacor_id).strip():
        return str(sivacor_id).strip()

    return ""


def get_info_from_jira(issue_key, keyword='doi'):
    """
    Get information from JIRA issue based on keyword.

    Args:
        issue_key: JIRA issue key (e.g., 'AEAREP-8361')
        keyword: Type of information to retrieve ('doi' or 'openicpsrurl')

    Returns:
        Requested information if found, empty string otherwise
    """
    # Get JIRA client
    jira = get_jira_client()
    if not jira:
        return ""

    try:
        # Get issue
        issue = jira.issue(issue_key)

        # Build field map
        field_map = build_field_map(jira)

        # Route to appropriate function based on keyword
        keyword_lower = keyword.lower()
        if keyword_lower == 'doi':
            return get_doi_from_jira(issue, field_map)
        elif keyword_lower == 'openicpsrurl':
            return get_openicpsr_url_from_jira(issue, field_map)
        elif keyword_lower == 'dcaf_private':
            return check_dcaf_private_data(issue, field_map)
        elif keyword_lower == 'mcid':
            return get_manuscript_central_id(issue, field_map)
        elif keyword_lower == 'mctitle':
            return get_manuscript_title(issue, field_map)
        elif keyword_lower == 'sivacorid':
            return get_sivacor_id(issue, field_map)
        else:
            print(f"Unknown keyword: {keyword}", file=sys.stderr)
            return ""

    except Exception:
        return ""


def print_help():
    """Print help message with available keywords."""
    help_text = """
JIRA Information Fetcher for AEA Data Editor

Usage:
    python3 jira_get_info.py <issue-key> [keyword]
    python3 jira_get_info.py -h|--help

Arguments:
    issue-key    JIRA issue key (e.g., aearep-8361, AEAREP-1234)
    keyword      Type of information to retrieve (optional, defaults to 'doi')

Available Keywords:
    doi          - DOI (from RepositoryDOI or constructed from openICPSR fields)
    openicpsrurl - openICPSR alternate URL
    dcaf_private - Check if DCAF_Access_Restrictions_V2 contains "Yes, data can be made available privately"
                   Returns "yes" if present, empty string otherwise
    mcid         - Manuscript Central Identifier
    mctitle      - Manuscript title (extracted from Description field)
    sivacorid    - SIVACOR ID

Examples:
    python3 jira_get_info.py aearep-8361 doi
    python3 jira_get_info.py aearep-8361 openicpsrurl
    python3 jira_get_info.py aearep-8361 dcaf_private
    python3 jira_get_info.py aearep-8361 mcid
    python3 jira_get_info.py aearep-8361 mctitle
    python3 jira_get_info.py aearep-8361 sivacorid
    python3 jira_get_info.py aearep-8361              # defaults to 'doi'

Environment Variables Required:
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens

    To obtain a JIRA API token:
    1. Visit https://id.atlassian.com/manage-profile/security/api-tokens
    2. Click "Create API token"
    3. Copy the token and set it as JIRA_API_KEY environment variable
"""
    print(help_text)


def main():
    # Handle help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_help()
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage: jira_get_info.py <issue-key> [keyword]", file=sys.stderr)
        print("       jira_get_info.py -h|--help", file=sys.stderr)
        print("", file=sys.stderr)
        print("Available keywords: doi, openicpsrurl, dcaf_private, mcid, mctitle, sivacorid", file=sys.stderr)
        sys.exit(1)

    issue_key = sys.argv[1].upper()
    keyword = sys.argv[2] if len(sys.argv) > 2 else 'doi'

    info = get_info_from_jira(issue_key, keyword)

    if info:
        print(info)


if __name__ == '__main__':
    main()
