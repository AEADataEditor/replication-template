#!/usr/bin/env python3
"""
Detect the software used in a deposit from a programs-metadata.csv (produced
by automations/04_list_program_files.sh) and update a Jira issue's
"Software used" field (customfield_10028) with any newly-identified names.

Usage:
    python3 jira_update_software.py <issue-key> <metadata-csv> [--project-dir DIR] [--yes]
    python3 jira_update_software.py -h|--help

Arguments:
    issue-key      Jira issue key (e.g., AEAREP-9354). Bare numbers are
                    expanded to AEAREP-<n>.
    metadata-csv    Path to generated/programs-metadata[.tag].csv.

Options:
    --project-dir DIR   Root directory the metadata CSV's paths are relative
                        to. Required to inspect .ipynb kernel language;
                        without it, notebooks are left unmatched.
    --lookup-ext CSV    Override the extension->software table (default:
                        software-extensions.csv next to this script).
    --lookup-name CSV   Override the filename->software table (default:
                        software-filenames.csv next to this script).
    --yes               Apply the update to Jira. Without this flag, the
                        script only prints what it would do (dry run).

Environment Variables Required (only when --yes is passed):
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens

Output:
    Prints detected software and any unmatched files (by extension) to
    stdout. Exit code 0 on success (including a no-op dry run), 1 on error.
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

JIRA_SERVER = "https://aeadataeditors.atlassian.net"
SOFTWARE_FIELD = "customfield_10028"

DEFAULT_EXT_LOOKUP = Path(__file__).resolve().parent / "software-extensions.csv"
DEFAULT_NAME_LOOKUP = Path(__file__).resolve().parent / "software-filenames.csv"

IPYNB_LANGUAGE_MAP = {
    "python": "Python",
    "python3": "Python",
    "r": "R",
    "ir": "R",
    "julia": "Julia",
}


def load_csv_lookup(path):
    """Load a two-column CSV (key,value) into a dict keyed by lower-cased first column."""
    lookup = {}
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            if not row:
                continue
            key, value = row[0], row[1]
            lookup[key.strip().lower()] = value.strip()
    return lookup


def detect_ipynb_language(path):
    """Return the canonical software name for a notebook's kernel language, or None."""
    try:
        with open(path, encoding="utf-8") as f:
            notebook = json.load(f)
    except (OSError, ValueError):
        return None

    metadata = notebook.get("metadata", {}) if isinstance(notebook, dict) else {}
    lang = None
    kernelspec = metadata.get("kernelspec")
    if isinstance(kernelspec, dict):
        lang = kernelspec.get("language")
    if not lang:
        language_info = metadata.get("language_info")
        if isinstance(language_info, dict):
            lang = language_info.get("name")
    if not lang:
        return None
    return IPYNB_LANGUAGE_MAP.get(str(lang).strip().lower())


def resolve_software(filenames, project_dir, ext_lookup, name_lookup):
    """
    Resolve a list of relative file paths (as found in programs-metadata.csv)
    to canonical software names.

    Returns (found: set[str], unmatched: dict[str, int]) where unmatched
    counts files that could not be mapped, keyed by extension (or basename
    when there is no extension).
    """
    found = set()
    unmatched = {}

    def record_unmatched(key):
        unmatched[key] = unmatched.get(key, 0) + 1

    for rel_path in filenames:
        rel_path = rel_path.strip()
        if not rel_path:
            continue
        basename = os.path.basename(rel_path)
        base_lower = basename.lower()
        ext = Path(basename).suffix.lstrip(".").lower()

        if base_lower in name_lookup:
            found.add(name_lookup[base_lower])
            continue

        if ext == "ipynb":
            lang = detect_ipynb_language(Path(project_dir) / rel_path) if project_dir is not None else None
            if lang:
                found.add(lang)
            else:
                record_unmatched("ipynb")
            continue

        if ext in ext_lookup:
            found.add(ext_lookup[ext])
            continue

        record_unmatched(ext if ext else base_lower)

    return found, unmatched


def read_metadata_filenames(metadata_csv):
    """Read the filename column of a generated/programs-metadata.csv file."""
    filenames = []
    with open(metadata_csv, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header: filename,lines
        for row in reader:
            if row:
                filenames.append(row[0])
    return filenames


def normalize_issue_key(key):
    """Expand a bare issue number to AEAREP-<n>; uppercase any other key as-is."""
    key = key.strip()
    if key.isdigit():
        return f"AEAREP-{key}"
    return key.upper()


def get_jira_client():
    """Initialize and return an authenticated Jira client, or None if creds/connection fail."""
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


def update_software_field(jira, issue_key, new_software):
    """
    Union new_software into the issue's current Software used labels and
    update Jira only if that grows the set.

    Returns (updated: bool, final_set: set[str], added: set[str]).
    """
    issue = jira.issue(issue_key)
    current = getattr(issue.fields, SOFTWARE_FIELD, None) or []
    current_set = set(current)
    union = current_set | set(new_software)
    added = union - current_set
    if added:
        issue.update(fields={SOFTWARE_FIELD: sorted(union)})
    return bool(added), union, added


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="jira_update_software.py",
        description="Detect software used from a programs-metadata.csv and update Jira's 'Software used' field.",
    )
    parser.add_argument("issue_key")
    parser.add_argument("metadata_csv")
    parser.add_argument(
        "--project-dir",
        default=None,
        help="Root directory the metadata CSV paths are relative to (needed to inspect .ipynb kernel language)",
    )
    parser.add_argument("--lookup-ext", default=str(DEFAULT_EXT_LOOKUP))
    parser.add_argument("--lookup-name", default=str(DEFAULT_NAME_LOOKUP))
    parser.add_argument("--yes", action="store_true", help="Apply the update to Jira (default is a dry run)")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.metadata_csv):
        print(f"Error: metadata CSV not found: {args.metadata_csv}", file=sys.stderr)
        return 1

    ext_lookup = load_csv_lookup(args.lookup_ext)
    name_lookup = load_csv_lookup(args.lookup_name)
    filenames = read_metadata_filenames(args.metadata_csv)

    found, unmatched = resolve_software(filenames, args.project_dir, ext_lookup, name_lookup)

    print(f"Software detected: {', '.join(sorted(found)) or '(none)'}")
    if unmatched:
        print("Files not mapped to any software (indeterminate/excluded), by extension:")
        for key, count in sorted(unmatched.items()):
            print(f"  {key}: {count} file(s)")

    if not found:
        print("No software detected; nothing to update.")
        return 0

    if not args.yes:
        print("Dry run (pass --yes to apply). Would add to Jira's Software used field:", ", ".join(sorted(found)))
        return 0

    jira = get_jira_client()
    if jira is None:
        return 1

    issue_key = normalize_issue_key(args.issue_key)

    try:
        updated, final_set, added = update_software_field(jira, issue_key, found)
    except Exception as e:
        print(f"Error: Failed to update {issue_key}: {e}", file=sys.stderr)
        return 1

    if updated:
        print(f"Updated {issue_key} Software used: added {', '.join(sorted(added))} (now: {', '.join(sorted(final_set))})")
    else:
        print(f"{issue_key} Software used already contains all detected software; no update needed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
