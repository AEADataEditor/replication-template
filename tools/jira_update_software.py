#!/usr/bin/env python3
"""
Detect the software used in a deposit from a programs-metadata.csv (produced
by automations/04_list_program_files.sh) and update a Jira issue's
"Software used" checkbox field with any newly-identified names, plus the
"Software used (other)" text field for anything that isn't a checkbox
option.

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
import time
from pathlib import Path

JIRA_SERVER = "https://aeadataeditors.atlassian.net"
CHECKBOX_FIELD_NAME = "Software used"
OTHER_FIELD_NAME = "Software used (other)"

# Jira Cloud intermittently rejects a field write with a "not on the
# appropriate screen" 400 even when the field is genuinely on the issue's
# edit screen (observed on AEAREP tickets of varying age, both touched and
# untouched) - a bare retry after a short delay has always cleared it in
# testing. Retry only this specific signature; any other error is a real
# failure and is not retried.
RETRY_DELAYS_SECONDS = (2, 5, 10)

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


def resolve_fields(jira):
    """Return (checkbox_field_id, other_field_id) by display name."""
    field_map = {field["name"]: field["id"] for field in jira.fields()}
    checkbox_id = field_map.get(CHECKBOX_FIELD_NAME)
    other_id = field_map.get(OTHER_FIELD_NAME)
    if not checkbox_id:
        raise RuntimeError(f"Could not find field '{CHECKBOX_FIELD_NAME}'")
    if not other_id:
        raise RuntimeError(f"Could not find field '{OTHER_FIELD_NAME}'")
    return checkbox_id, other_id


def fetch_checkbox_options(jira, issue, checkbox_field_id):
    """Fetch the checkbox field's configured option labels via the issue's editmeta."""
    meta = jira.editmeta(issue)
    field_meta = meta.get("fields", {}).get(checkbox_field_id)
    if not field_meta:
        return set()
    return {opt["value"] for opt in field_meta.get("allowedValues", [])}


def _is_transient_screen_error(exc, field_ids):
    """True if exc is the intermittent Jira Cloud 'field not on screen' 400 for one of field_ids."""
    text = getattr(exc, "text", None) or ""
    return (
        getattr(exc, "status_code", None) == 400
        and any(field_id in text for field_id in field_ids)
        and "not on the appropriate screen" in text
    )


def update_software_field(jira, issue_key, new_software, retry_delays=RETRY_DELAYS_SECONDS, sleep=time.sleep):
    """
    Partition new_software into checkbox-valid and invalid (not a configured
    checkbox option), union the valid ones into the checkbox field and the
    invalid ones into the "other" text field, and update Jira only if that
    changes either field. When invalid values are recorded, also posts an
    issue comment noting they weren't a checkbox option.

    Retries the write on Jira's intermittent transient screen-validation
    error (see RETRY_DELAYS_SECONDS), sleeping between attempts via `sleep`
    (overridable for tests). Any other error, or exhausting all retries,
    propagates to the caller.

    Returns (updated: bool, final_checkbox: set[str], added_checkbox: set[str], invalid: set[str]).
    """
    from jira.exceptions import JIRAError

    checkbox_id, other_id = resolve_fields(jira)
    issue = jira.issue(issue_key)

    checkbox_options = fetch_checkbox_options(jira, issue, checkbox_id)
    current_checkbox = {opt.value for opt in (getattr(issue.fields, checkbox_id, None) or [])}
    current_other = getattr(issue.fields, other_id, None) or ""
    current_other_values = {v.strip() for v in current_other.split(",") if v.strip()}

    valid = {name for name in new_software if name in checkbox_options}
    invalid = {name for name in new_software if name not in checkbox_options}

    final_checkbox = current_checkbox | valid
    final_other_values = current_other_values | invalid
    final_other = ", ".join(sorted(final_other_values))

    added_checkbox = final_checkbox - current_checkbox
    updated = final_checkbox != current_checkbox or final_other != current_other

    if updated:
        fields = {}
        if final_checkbox != current_checkbox:
            fields[checkbox_id] = [{"value": v} for v in sorted(final_checkbox)]
        if final_other != current_other:
            fields[other_id] = final_other

        remaining_delays = list(retry_delays)
        while True:
            try:
                issue.update(fields=fields)
                break
            except JIRAError as e:
                if remaining_delays and _is_transient_screen_error(e, (checkbox_id, other_id)):
                    sleep(remaining_delays.pop(0))
                    continue
                raise

        if invalid:
            jira.add_comment(
                issue,
                f"Detected software not in the '{CHECKBOX_FIELD_NAME}' checkbox options, "
                f"recorded in '{OTHER_FIELD_NAME}' instead: {', '.join(sorted(invalid))}",
            )

    return updated, final_checkbox, added_checkbox, invalid


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

    print(f"Software detected: {' '.join(sorted(found)) or '(none)'}")
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
        updated, final_checkbox, added_checkbox, invalid = update_software_field(jira, issue_key, found)
    except Exception as e:
        print(f"Error: Failed to update {issue_key}: {e}", file=sys.stderr)
        return 1

    if updated:
        note = f"added {', '.join(sorted(added_checkbox))}" if added_checkbox else "no new checkbox values"
        print(f"Updated {issue_key} Software used: {note} (now: {', '.join(sorted(final_checkbox))})")
        if invalid:
            print(f"  Also recorded in '{OTHER_FIELD_NAME}' and commented: {', '.join(sorted(invalid))}")
    else:
        print(f"{issue_key} Software used already contains all detected software; no update needed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
