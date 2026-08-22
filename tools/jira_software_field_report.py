#!/usr/bin/env python3
"""
Report live usage frequency of the "Software used" Jira field (customfield_10028)
across all AEAREP issues, to decide the option list for the new checkbox field
that will replace it.

Usage:
    python3 jira_software_field_report.py [--threshold PERCENT]
    python3 jira_software_field_report.py -h|--help

Options:
    --threshold PERCENT   Minimum percent of tickets-with-field-set a value
                          must reach to be listed as a checkbox candidate
                          (default: 5).

Environment Variables Required:
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens

Output:
    Prints a frequency table (sorted by declining count), split into
    checkbox candidates (>= threshold) and rare values (< threshold), plus
    any raw values that don't normalize to a known canonical software name.
    Read-only: makes no changes to Jira. Exit code 0 on success, 1 on error.
"""

import argparse
import csv
import os
import sys
from pathlib import Path

JIRA_SERVER = "https://aeadataeditors.atlassian.net"
FIELD_NAME = "Software used"

DEFAULT_EXT_LOOKUP = Path(__file__).resolve().parent / "software-extensions.csv"
DEFAULT_NAME_LOOKUP = Path(__file__).resolve().parent / "software-filenames.csv"

# Stray casing variants observed in the live field beyond what the
# extension/filename tables themselves imply canonical names for.
EXTRA_ALIASES = {
    "matlab": "MATLAB",
    "stata": "Stata",
    "python": "Python",
    "r": "R",
    "sas": "SAS",
    "julia": "Julia",
    "dynare": "Dynare",
    "unknown": "Unknown",
}


def load_canonical_names(ext_csv, name_csv):
    """Collect the set of canonical software names this repo already recognizes."""
    names = set()
    for csv_path in (ext_csv, name_csv):
        with open(csv_path, newline="") as f:
            reader = csv.reader(f)
            next(reader, None)  # header
            for row in reader:
                if row:
                    names.add(row[1].strip())
    return names


def build_alias_map(canonical_names):
    """Map lower-cased name -> canonical name, for normalizing raw field values."""
    alias_map = {name.lower(): name for name in canonical_names}
    alias_map.update(EXTRA_ALIASES)
    return alias_map


def normalize(raw_value, alias_map):
    """Return (canonical_name, was_recognized: bool)."""
    key = raw_value.strip().lower()
    if key in alias_map:
        return alias_map[key], True
    return raw_value.strip(), False


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


def resolve_field_id(jira, field_name):
    for field in jira.fields():
        if field["name"] == field_name:
            return field["id"]
    return None


def fetch_field_values(jira, field_id):
    """Yield the raw label list of `field_id` for every AEAREP issue that has it set."""
    cf_number = field_id.replace("customfield_", "")
    jql = f'project = AEAREP AND cf[{cf_number}] is not EMPTY ORDER BY key'
    issues = jira.enhanced_search_issues(jql, maxResults=False, fields=field_id)
    for issue in issues:
        values = getattr(issue.fields, field_id, None) or []
        yield issue.key, values


def tally(jira, field_id, alias_map):
    """Return (counts: dict[name,int], tickets_with_field: int, unrecognized: dict[str,int])."""
    counts = {}
    unrecognized = {}
    tickets_with_field = 0
    for _issue_key, values in fetch_field_values(jira, field_id):
        if not values:
            continue
        tickets_with_field += 1
        for raw in values:
            canonical, recognized = normalize(raw, alias_map)
            counts[canonical] = counts.get(canonical, 0) + 1
            if not recognized:
                unrecognized[raw] = unrecognized.get(raw, 0) + 1
    return counts, tickets_with_field, unrecognized


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="jira_software_field_report.py",
        description="Report live usage frequency of the 'Software used' Jira field.",
    )
    parser.add_argument("--threshold", type=float, default=5.0, help="Checkbox-candidate cutoff, percent (default: 5)")
    parser.add_argument("--lookup-ext", default=str(DEFAULT_EXT_LOOKUP))
    parser.add_argument("--lookup-name", default=str(DEFAULT_NAME_LOOKUP))
    args = parser.parse_args(argv)

    jira = get_jira_client()
    if jira is None:
        return 1

    field_id = resolve_field_id(jira, FIELD_NAME)
    if field_id is None:
        print(f"Error: could not find a field named '{FIELD_NAME}'", file=sys.stderr)
        return 1

    canonical_names = load_canonical_names(args.lookup_ext, args.lookup_name)
    alias_map = build_alias_map(canonical_names)

    counts, tickets_with_field, unrecognized = tally(jira, field_id, alias_map)

    if tickets_with_field == 0:
        print(f"No AEAREP issues have '{FIELD_NAME}' ({field_id}) set.")
        return 0

    print(f"Field: {FIELD_NAME} ({field_id})")
    print(f"Tickets with field set: {tickets_with_field}")
    print()

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    checkbox_candidates = []
    rare = []
    print(f"{'Value':<15} {'Count':>6} {'% of tickets':>13}  Candidate")
    for name, count in ranked:
        pct = 100.0 * count / tickets_with_field
        is_candidate = pct >= args.threshold
        (checkbox_candidates if is_candidate else rare).append((name, count, pct))
        label = "checkbox" if is_candidate else "other (rare)"
        print(f"{name:<15} {count:>6} {pct:>12.1f}%  {label}")

    print()
    print(f"Checkbox candidates (>= {args.threshold}%), in declining-frequency order:")
    for name, count, pct in checkbox_candidates:
        print(f"  {name} ({count}, {pct:.1f}%)")

    print()
    print(f"Rare values (< {args.threshold}%, would land in 'other'):")
    for name, count, pct in rare:
        print(f"  {name} ({count}, {pct:.1f}%)")

    if unrecognized:
        print()
        print("Raw values that did not normalize to a known canonical name (review for typos/new tools):")
        for raw, count in sorted(unrecognized.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {raw!r} ({count})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
