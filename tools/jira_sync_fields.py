#!/usr/bin/env python3
"""
Sync fields from a source Jira issue to a target issue,
only updating fields that are empty/null on the target.

Usage:
    python3 jira_sync_fields.py <issue-key> [<target-key>] [--yes]
    python3 jira_sync_fields.py -h|--help

Arguments:
    issue-key    Jira issue key to sync from/to (e.g., AEAREP-9603 or 9603).
                 If <target-key> is provided, this is the source issue to copy fields from.
                 If <target-key> is omitted, this is treated as the revision issue (target)
                 and the linked original is auto-detected as the source.
    target-key   Optional explicit target issue key to copy fields to.
                 If omitted, auto-detected via an "is a revision of" link on <issue-key>.
                 Exactly one such link must exist.
    Issue keys may be given as bare numbers (e.g., 9603), in which case
    "AEAREP-" is prepended automatically.  Keys that already carry a project
    prefix (e.g., TRAIN-2000) are used as-is.

Options:
    -y, --yes        Apply changes without prompting for confirmation
    -c, --comment    Post a comment to the target issue listing all synced fields

Output:
    Prints a preview of fields to be transferred, prompts for confirmation
    (unless --yes is given), then prints a summary of fields actually synced.
    Exit code 0 on success, 1 on usage error

Environment Variables Required:
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens

    To obtain a JIRA API token:
    1. Visit https://id.atlassian.com/manage-profile/security/api-tokens
    2. Click "Create API token"
    3. Copy the token and set it as JIRA_API_KEY environment variable

Examples:
    python3 jira_sync_fields.py AEAREP-9000 AEAREP-9603
    python3 jira_sync_fields.py 9000 9603
    python3 jira_sync_fields.py AEAREP-9603          # 9603 is new revision; original auto-detected as source
    python3 jira_sync_fields.py 9603 --yes
    python3 jira_sync_fields.py 9000 9603 --comment  # post comment listing synced fields
"""

import argparse
import os
import sys
from jira import JIRA

JIRA_SERVER = "https://aeadataeditors.atlassian.net"

# Fields to skip (system-managed or non-transferable)
SKIP_FIELDS = {
    "statuscategorychangedate",
    "issuetype",
    "project",
    "workratio",
    "watches",
    "created",
    "updated",
    "timetracking",
    "attachment",
    "issuelinks",
    "subtasks",
    "status",
    "creator",
    "reporter",
    "aggregateprogress",
    "progress",
    "votes",
    "comment",
    "worklog",
    "key",
    "id",
    "self",
    "expand",
    "changelog",
    "resolution",
    "resolutiondate",
    "lastViewed",
    "thumbnail",
}

# Fields that are legitimately empty on a new/revision issue and should never
# be copied from the source even when blank on the target.
EXEMPT_FIELDS = {
    "MCRecommendationV2",
}


def get_jira_client():
    """Initialize and return authenticated Jira client."""
    jira_username = os.environ.get('JIRA_USERNAME')
    jira_api_key = os.environ.get('JIRA_API_KEY')

    if not jira_username or not jira_api_key:
        return None

    try:
        return JIRA(
            server=JIRA_SERVER,
            basic_auth=(jira_username, jira_api_key),
            options={'verify': True}
        )
    except Exception:
        return None


def normalize_issue_key(key: str) -> str:
    """Normalise a user-supplied issue key.

    - Bare numbers (e.g. '9603') are expanded to 'AEAREP-9603'.
    - Keys with any non-numeric prefix (e.g. 'train-2000', 'AEAREP-9000')
      are returned uppercased as-is.
    """
    key = key.strip()
    if key.isdigit():
        return f"AEAREP-{key}"
    return key.upper()


def fetch_issue(jira, issue_key: str) -> object:
    """Fetch a Jira issue object."""
    return jira.issue(issue_key, expand='names')


def find_revision_link(issue) -> list:
    """Return issue keys linked to *issue* via an 'is a revision of' link type.

    Checks both inward and outward directions for any link whose type name or
    inward/outward description contains the word 'revision' (case-insensitive).
    Returns a list of issue key strings.
    """
    linked_keys = []
    issuelinks = getattr(issue.fields, 'issuelinks', []) or []
    for link in issuelinks:
        link_type = link.type
        type_text = ' '.join([
            getattr(link_type, 'name', ''),
            getattr(link_type, 'inward', ''),
            getattr(link_type, 'outward', ''),
        ]).lower()
        if 'revision' not in type_text:
            continue
        inward_issue = getattr(link, 'inwardIssue', None)
        outward_issue = getattr(link, 'outwardIssue', None)
        if inward_issue:
            linked_keys.append(inward_issue.key)
        if outward_issue:
            linked_keys.append(outward_issue.key)
    return linked_keys


def is_empty(value) -> bool:
    """Check if a field value is effectively empty."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    if isinstance(value, dict) and not value:
        return True
    # ADF empty doc check (description, etc.)
    if isinstance(value, dict) and value.get("type") == "doc":
        content = value.get("content", [])
        if not content:
            return True
        # A doc with a single empty paragraph
        if (
            len(content) == 1
            and content[0].get("type") == "paragraph"
            and not content[0].get("content")
        ):
            return True
    return False


def build_update_payload(source_fields: dict, target_fields: dict, field_names: dict) -> dict:
    """
    Compare source and target fields. Return an update payload
    containing only fields that are empty on the target but
    populated on the source, excluding SKIP_FIELDS and EXEMPT_FIELDS.
    """
    update = {}

    # Build a case-insensitive lookup for exempt field display names
    exempt_lower = {f.lower() for f in EXEMPT_FIELDS}

    for field_key, source_value in source_fields.items():
        # Skip system/non-transferable fields
        if field_key in SKIP_FIELDS:
            continue
        # Skip fields that are legitimately empty on a revision issue.
        # Check both the raw key and the human-readable display name.
        display_name = field_names.get(field_key, field_key)
        if field_key.lower() in exempt_lower or display_name.lower() in exempt_lower:
            continue

        target_value = target_fields.get(field_key)

        # Only transfer if target is empty and source is not
        if is_empty(target_value) and not is_empty(source_value):
            update[field_key] = source_value

    return update


def format_for_display(value, max_len: int = 80) -> str:
    """Return a human-readable string for a Jira field value (display only).

    Handles single-select options, multi-select lists, user objects, and
    plain scalars.  Always returns a plain string.
    """
    def _scalar(v) -> str:
        """Extract the best human-readable token from a single Jira value."""
        if v is None:
            return ""
        if isinstance(v, dict):
            # Prefer: value (option) > displayName (user) > name (status/priority)
            for key in ('value', 'displayName', 'name'):
                if v.get(key):
                    return str(v[key])
            # ADF doc: just signal it has content
            if v.get('type') == 'doc':
                return '<rich text>'
            return '<object>'
        return str(v)

    if isinstance(value, list):
        parts = [_scalar(item) for item in value if not is_empty(item)]
        result = ', '.join(parts)
    else:
        result = _scalar(value)

    if len(result) > max_len:
        result = result[:max_len - 3] + '...'
    return result


def update_issue(jira, issue_key: str, payload: dict):
    """Update a Jira issue with the given field payload."""
    try:
        issue = jira.issue(issue_key)
        issue.update(fields=payload)
    except Exception as e:
        print(f"Failed to update {issue_key}: {e}", file=sys.stderr)
        sys.exit(1)


def post_comment(jira, issue_key: str, source_key: str, synced: dict, field_names: dict):
    """Post a comment to issue_key listing the fields synced from source_key."""
    lines = [f"Fields synced from {source_key}:"]
    for field_key in sorted(synced.keys()):
        name = field_names.get(field_key, field_key)
        preview = format_for_display(synced[field_key], max_len=120)
        lines.append(f"  - {name}: {preview}")
    comment_text = "\n".join(lines)
    try:
        jira.add_comment(issue_key, comment_text)
        print(f"Comment posted to {issue_key}")
    except Exception as e:
        print(f"Warning: could not post comment to {issue_key}: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        prog='jira_sync_fields.py',
        description='Sync fields from a source Jira issue to a target issue (empty fields only).',
        epilog='Environment: JIRA_USERNAME, JIRA_API_KEY',
    )
    parser.add_argument(
        'source_key',
        metavar='issue-key',
        help=(
            'Jira issue key (or bare number). If <target-key> is provided, this is the source issue; '
            'otherwise this is treated as the revision issue (target) and the source is auto-detected.'
        ),
    )
    parser.add_argument(
        'target_key',
        metavar='target-key',
        nargs='?',
        default=None,
        help=(
            'Optional explicit target issue key (or bare number). If omitted, the source issue is auto-detected '
            'via an "is a revision of" link on <issue-key>.'
        ),
    )
    parser.add_argument('-y', '--yes', action='store_true',
                        help='Apply changes without prompting for confirmation')
    parser.add_argument('-c', '--comment', action='store_true',
                        help='Post a comment to the target issue listing all synced fields')
    args = parser.parse_args()

    source_key = normalize_issue_key(args.source_key)

    jira = get_jira_client()
    if not jira:
        print("Error: JIRA_USERNAME and JIRA_API_KEY environment variables are required.", file=sys.stderr)
        sys.exit(1)

    # Fetch the user-supplied key first (needed for revision-link lookup)
    supplied_key = source_key
    try:
        print(f"Fetching {supplied_key}...")
        supplied_issue = fetch_issue(jira, supplied_key)
    except Exception as e:
        print(f"Error fetching {supplied_key}: {e}", file=sys.stderr)
        sys.exit(1)

    # Resolve source / target
    if args.target_key:
        # Explicit two-key mode: supplied key is source, second arg is target
        target_key = normalize_issue_key(args.target_key)
        source_key = supplied_key
        try:
            print(f"Fetching {target_key}...")
            target = fetch_issue(jira, target_key)
        except Exception as e:
            print(f"Error fetching {target_key}: {e}", file=sys.stderr)
            sys.exit(1)
        source = supplied_issue
    else:
        # Auto-detect mode: supplied key is the NEW revision (target);
        # the linked original becomes the source.
        revision_links = find_revision_link(supplied_issue)
        if len(revision_links) == 0:
            print(f"Error: no 'is a revision of' link found on {supplied_key}. "
                  "Please provide the target-key explicitly.", file=sys.stderr)
            sys.exit(1)
        if len(revision_links) > 1:
            keys = ', '.join(revision_links)
            print(f"Error: multiple revision links found on {supplied_key}: {keys}. "
                  "Please provide the target-key explicitly.", file=sys.stderr)
            sys.exit(1)
        source_key = revision_links[0]
        target_key = supplied_key
        print(f"Auto-detected source: {source_key}")
        try:
            print(f"Fetching {source_key}...")
            source = fetch_issue(jira, source_key)
        except Exception as e:
            print(f"Error fetching {source_key}: {e}", file=sys.stderr)
            sys.exit(1)
        target = supplied_issue

    print(f"Syncing fields: {source_key} -> {target_key}")
    print("(Only empty fields on the target will be updated)\n")

    source_fields = source.raw["fields"]
    target_fields = target.raw["fields"]

    # Get field name mapping for readable output
    field_names = source.raw.get("names", {})

    # Build the update payload
    payload = build_update_payload(source_fields, target_fields, field_names)

    if not payload:
        print("Nothing to transfer -- all target fields are already populated.")
        return

    # Preview changes
    print(f"\nFields to transfer ({len(payload)}):")
    for field_key in sorted(payload.keys()):
        name = field_names.get(field_key, field_key)
        value = payload[field_key]
        preview = format_for_display(value)
        print(f"  {name}: {preview}")

    # Confirm before applying
    if not args.yes:
        confirm = input(f"\nApply these {len(payload)} changes to {target_key}? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            return

    update_issue(jira, target_key, payload)

    # Summary
    print(f"\nSummary: {len(payload)} field(s) synced from {source_key} to {target_key}:")
    for field_key in sorted(payload.keys()):
        name = field_names.get(field_key, field_key)
        print(f"  - {name}")

    if args.comment:
        post_comment(jira, target_key, source_key, payload, field_names)


if __name__ == "__main__":
    main()