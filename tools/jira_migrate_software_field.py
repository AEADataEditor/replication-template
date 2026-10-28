#!/usr/bin/env python3
"""
Migrate values from the retired "Software used (v1)" labels field
(customfield_10028) into the new "Software used" checkboxes field and
"Software used (other)" text field, for every AEAREP issue that has v1 set.

Normalized values that match one of the new checkbox field's configured
options are written there; anything else is appended (deduped) to the
"other" text field. "Software used (v1)" itself is never modified.

Usage:
    python3 jira_migrate_software_field.py [--yes] [--issue KEY ...]
    python3 jira_migrate_software_field.py -h|--help

Options:
    --yes           Apply updates to Jira. Without this flag, the script
                     only prints what it would do (dry run).
    --issue KEY     Limit migration to specific issue key(s) (repeatable).
                     Default: every AEAREP issue with "Software used (v1)" set.

Environment Variables Required (only when --yes is passed):
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens

Output:
    Per-issue before/after summary, then a final tally of issues touched
    and any raw values that didn't normalize to a known canonical name
    (flagged for manual review, still recorded verbatim in "other").
    Exit code 0 on success (including a no-op dry run), 1 on error.
"""

import argparse
import os
import sys

JIRA_SERVER = "https://aeadataeditors.atlassian.net"
V1_FIELD_NAME = "Software used (v1)"
CHECKBOX_FIELD_NAME = "Software used"
OTHER_FIELD_NAME = "Software used (other)"

# Stray casing variants observed in the live v1 field beyond what the
# extension/filename tables themselves imply canonical names for.
EXTRA_ALIASES = {
    "matlab": "MATLAB",
    "stata": "Stata",
    "python": "Python",
    "r": "R",
    "sas": "SAS",
    "julia": "Julia",
}


def normalize(raw_value, alias_map):
    key = raw_value.strip().lower()
    return alias_map.get(key, raw_value.strip())


def get_jira_client():
    jira_username = os.environ.get("JIRA_USERNAME")
    jira_api_key = os.environ.get("JIRA_API_KEY")

    if not jira_username or not jira_api_key:
        print("Error: JIRA_USERNAME and JIRA_API_KEY environment variables must be set", file=sys.stderr)
        return None

    from jira import JIRA

    try:
        return JIRA(server=JIRA_SERVER, basic_auth=(jira_username, jira_api_key), options={"verify": True})
    except Exception as e:
        print(f"Error: Failed to connect to Jira: {e}", file=sys.stderr)
        return None


def resolve_fields(jira):
    """Return (v1_field_id, checkbox_field_id, other_field_id, checkbox_options: set[str])."""
    field_map = {field["name"]: field["id"] for field in jira.fields()}

    v1_id = field_map.get(V1_FIELD_NAME)
    checkbox_id = field_map.get(CHECKBOX_FIELD_NAME)
    other_id = field_map.get(OTHER_FIELD_NAME)

    checkbox_options = fetch_checkbox_options(jira, checkbox_id) if checkbox_id else set()

    return v1_id, checkbox_id, other_id, checkbox_options


def fetch_checkbox_options(jira, checkbox_field_id):
    """Fetch the checkbox field's configured option labels via a sample issue's editmeta."""
    jql = f"project = AEAREP ORDER BY key DESC"
    issues = jira.enhanced_search_issues(jql, maxResults=1, fields=checkbox_field_id)
    if not issues:
        return set()
    meta = jira.editmeta(issues[0])
    field_meta = meta.get("fields", {}).get(checkbox_field_id)
    if not field_meta:
        return set()
    return {opt["value"] for opt in field_meta.get("allowedValues", [])}


def alias_map_from_options(checkbox_options):
    alias_map = {name.lower(): name for name in checkbox_options}
    alias_map.update({k: v for k, v in EXTRA_ALIASES.items() if v in checkbox_options})
    return alias_map


def fetch_issues_with_v1(jira, v1_field_id, checkbox_field_id, other_field_id, issue_keys=None):
    if issue_keys:
        jql = f"key in ({', '.join(issue_keys)})"
    else:
        cf_number = v1_field_id.replace("customfield_", "")
        jql = f"project = AEAREP AND cf[{cf_number}] is not EMPTY ORDER BY key"
    fields = [v1_field_id, checkbox_field_id, other_field_id]
    return jira.enhanced_search_issues(jql, maxResults=False, fields=fields)


def plan_migration(v1_values, checkbox_options, alias_map, existing_other):
    """Return (checkbox_values: set[str], other_values: set[str], unrecognized: set[str])."""
    checkbox_values = set()
    other_values = set(v.strip() for v in (existing_other or "").split(",") if v.strip())
    unrecognized = set()
    for raw in v1_values:
        canonical = normalize(raw, alias_map)
        if canonical in checkbox_options:
            checkbox_values.add(canonical)
        else:
            other_values.add(canonical)
            if canonical.lower() not in alias_map and canonical not in checkbox_options:
                unrecognized.add(raw.strip())
    return checkbox_values, other_values, unrecognized


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="jira_migrate_software_field.py",
        description="Migrate 'Software used (v1)' values into the new checkbox and 'other' fields.",
    )
    parser.add_argument("--yes", action="store_true", help="Apply updates to Jira (default is a dry run)")
    parser.add_argument("--issue", action="append", default=None, help="Limit to specific issue key(s)")
    args = parser.parse_args(argv)

    jira = get_jira_client()
    if jira is None:
        return 1

    v1_id, checkbox_id, other_id, checkbox_options = resolve_fields(jira)
    if not v1_id:
        print(f"Error: could not find field '{V1_FIELD_NAME}'", file=sys.stderr)
        return 1
    if not checkbox_id:
        print(f"Error: could not find field '{CHECKBOX_FIELD_NAME}'", file=sys.stderr)
        return 1
    if not other_id:
        print(f"Error: could not find field '{OTHER_FIELD_NAME}'", file=sys.stderr)
        return 1
    if not checkbox_options:
        print(f"Error: could not read allowed options for '{CHECKBOX_FIELD_NAME}'", file=sys.stderr)
        return 1

    alias_map = alias_map_from_options(checkbox_options)

    issue_keys = [k.upper() for k in args.issue] if args.issue else None
    issues = fetch_issues_with_v1(jira, v1_id, checkbox_id, other_id, issue_keys)

    touched = 0
    all_unrecognized = {}

    for issue in issues:
        v1_values = getattr(issue.fields, v1_id, None) or []
        if not v1_values:
            continue

        current_checkbox = {opt.value for opt in (getattr(issue.fields, checkbox_id, None) or [])}
        current_other = getattr(issue.fields, other_id, None) or ""

        checkbox_values, other_values, unrecognized = plan_migration(
            v1_values, checkbox_options, alias_map, current_other
        )

        new_checkbox = current_checkbox | checkbox_values
        new_other = ", ".join(sorted(other_values))

        changed = new_checkbox != current_checkbox or new_other != current_other
        if not changed:
            continue

        touched += 1
        for raw in unrecognized:
            all_unrecognized[raw] = all_unrecognized.get(raw, 0) + 1

        print(f"{issue.key}: v1={sorted(v1_values)}")
        if new_checkbox != current_checkbox:
            print(f"  checkbox: {sorted(current_checkbox)} -> {sorted(new_checkbox)}")
        if new_other != current_other:
            print(f"  other: {current_other!r} -> {new_other!r}")

        if args.yes:
            fields = {}
            if new_checkbox != current_checkbox:
                fields[checkbox_id] = [{"value": v} for v in sorted(new_checkbox)]
            if new_other != current_other:
                fields[other_id] = new_other
            try:
                issue.update(fields=fields)
            except Exception as e:
                print(f"  Error: failed to update {issue.key}: {e}", file=sys.stderr)

    print()
    print(f"{'Applied' if args.yes else 'Would apply'} changes to {touched} issue(s).")
    if all_unrecognized:
        print("Raw values that didn't normalize to a checkbox option (recorded in 'other' verbatim):")
        for raw, count in sorted(all_unrecognized.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {raw!r} ({count})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
