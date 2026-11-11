#!/usr/bin/env python3
"""
Compute the size of a downloaded deposit and record it (in MB) on a Jira
issue's "Deposit size" custom field. Always overwrites the field - ingest
pipelines can run multiple times and the field should reflect the latest run.

Usage:
    python3 jira_update_deposit_size.py <issue-key> <project-dir> [--yes]
    python3 jira_update_deposit_size.py -h|--help

Arguments:
    issue-key      Jira issue key (e.g., AEAREP-9354). Bare numbers are
                    expanded to AEAREP-<n>.
    project-dir    Directory the deposit was unpacked into.

Size source (checked in this order):
    1. If the deposit's unpacked directory contains exactly one ZIP file at
       its top level (the "single inner ZIP" case handled by
       automations/00_unpack_zip.sh), that ZIP's uncompressed size is used.
    2. Else, if a ZIP file was downloaded and left at the top level of the
       current directory (the envelope, before it is moved into cache/),
       that ZIP's uncompressed size is used.
    3. Else (no ZIP was downloaded at all, e.g. Zenodo), the on-disk size of
       project-dir is used.

Options:
    --yes    Apply the update to Jira. Without this flag, the script only
             prints what it would do (dry run).

Environment Variables Required (only when --yes is passed):
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens

Output:
    Prints the computed size and source to stdout. Exit code 0 on success,
    1 on error.
"""

import argparse
import os
import sys
import time
import zipfile
from pathlib import Path

JIRA_SERVER = "https://aeadataeditors.atlassian.net"
DEPOSIT_SIZE_FIELD_NAME = "Deposit size"
BYTES_PER_MB = 1024 * 1024

# Jira Cloud intermittently rejects a field write with a "not on the
# appropriate screen" 400 even when the field is genuinely on the issue's
# edit screen (see the same workaround in jira_update_software.py). A bare
# retry after a short delay has cleared it in testing there; keep the same
# delays here for parity.
RETRY_DELAYS_SECONDS = (2, 5, 10)


def find_top_level_zips(directory):
    """ZIP files directly inside directory (not recursive), sorted by name."""
    return sorted(p for p in Path(directory).iterdir() if p.is_file() and p.suffix.lower() == ".zip")


def uncompressed_zip_size(zip_path):
    """Sum of uncompressed file sizes recorded in a ZIP's central directory."""
    with zipfile.ZipFile(zip_path) as zf:
        return sum(info.file_size for info in zf.infolist())


def on_disk_size(directory):
    """Sum of file sizes under directory (symlinks excluded)."""
    total = 0
    for root, _dirs, files in os.walk(directory):
        for name in files:
            path = os.path.join(root, name)
            if not os.path.islink(path):
                total += os.path.getsize(path)
    return total


def compute_deposit_size_bytes(project_dir, cwd="."):
    """
    Determine the deposit's size in bytes and how it was determined.

    Returns (size_bytes: int, source: str).
    """
    inner_zips = find_top_level_zips(project_dir) if os.path.isdir(project_dir) else []
    if len(inner_zips) == 1:
        return uncompressed_zip_size(inner_zips[0]), f"single inner ZIP ({inner_zips[0]})"

    envelope_zips = find_top_level_zips(cwd)
    if envelope_zips:
        total = sum(uncompressed_zip_size(z) for z in envelope_zips)
        names = ", ".join(str(z) for z in envelope_zips)
        return total, f"envelope ZIP ({names})"

    return on_disk_size(project_dir), f"on-disk size of {project_dir}"


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


def resolve_field_id(jira, field_name):
    """Look up a custom field's id by its display name, or None if not found."""
    try:
        for field in jira.fields():
            if field["name"] == field_name:
                return field["id"]
    except Exception:
        pass
    return None


def _is_transient_screen_error(exc, field_id):
    """True if exc is Jira's intermittent 'field not on screen' 400 for field_id."""
    text = getattr(exc, "text", None) or ""
    return (
        getattr(exc, "status_code", None) == 400
        and field_id in text
        and "not on the appropriate screen" in text
    )


def update_deposit_size_field(jira, issue_key, size_mb, field_name=DEPOSIT_SIZE_FIELD_NAME,
                               retry_delays=RETRY_DELAYS_SECONDS, sleep=time.sleep):
    """
    Unconditionally overwrite the Deposit size field on issue_key with size_mb.

    Retries on Jira's intermittent transient "not on the appropriate screen"
    400 (see RETRY_DELAYS_SECONDS). Some issues reject the write with that
    same error for the pipeline's API user even though the field is on-screen
    interactively - unlike the transient case, retries won't clear this, so
    once they're exhausted the value is posted as an issue comment instead
    (mirrors jira_update_software.py's fallback for the "Software used
    (other)" field) so it isn't silently lost.

    Returns True if the field itself was updated, False if the comment
    fallback was used instead. Any other Jira error propagates.
    """
    from jira.exceptions import JIRAError

    field_id = resolve_field_id(jira, field_name)
    if field_id is None:
        raise RuntimeError(f"Jira field '{field_name}' not found")

    issue = jira.issue(issue_key)

    remaining_delays = list(retry_delays)
    while True:
        try:
            issue.update(fields={field_id: size_mb})
            return True
        except JIRAError as e:
            if not _is_transient_screen_error(e, field_id):
                raise
            if remaining_delays:
                sleep(remaining_delays.pop(0))
                continue
            jira.add_comment(
                issue,
                f"{field_name}: {size_mb} MB (could not be recorded in the '{field_name}' "
                f"field - it is not on this issue's edit screen for this Jira account).",
            )
            return False


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="jira_update_deposit_size.py",
        description="Compute deposit size and record it (in MB) on Jira's 'Deposit size' field.",
    )
    parser.add_argument("issue_key")
    parser.add_argument("project_dir")
    parser.add_argument("--yes", action="store_true", help="Apply the update to Jira (default is a dry run)")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.project_dir):
        print(f"Error: project directory not found: {args.project_dir}", file=sys.stderr)
        return 1

    size_bytes, source = compute_deposit_size_bytes(args.project_dir)
    size_mb = round(size_bytes / BYTES_PER_MB, 2)

    print(f"Deposit size: {size_mb} MB (source: {source})")

    if not args.yes:
        print("Dry run (pass --yes to apply). Would set Jira's Deposit size field to:", size_mb)
        return 0

    jira = get_jira_client()
    if jira is None:
        return 1

    issue_key = normalize_issue_key(args.issue_key)

    try:
        recorded = update_deposit_size_field(jira, issue_key, size_mb)
    except Exception as e:
        print(f"Error: Failed to update {issue_key}: {e}", file=sys.stderr)
        return 1

    if recorded:
        print(f"Updated {issue_key} Deposit size to {size_mb} MB")
    else:
        print(f"{issue_key} Deposit size field is not on the edit screen; "
              f"posted {size_mb} MB as a comment instead")
    return 0


if __name__ == "__main__":
    sys.exit(main())
