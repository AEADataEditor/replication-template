#!/usr/bin/env python3
"""
Zenodo download orchestrator.

Parses a Zenodo URL, DOI, or record ID and routes the download to either
download_zenodo_public.py (public records) or download_zenodo_draft.py
(draft deposits and community-review requests).

When no --zenodo-id is given, queries the Jira ticket for the
"Replication package URL".  If --zenodo-id is given, Jira and config.yml
lookups are skipped.

Usage:
    python3 tools/download_zenodo.py [--zenodo-id URL_OR_ID] [--jira-ticket KEY] [--print-id]

Options:
    --zenodo-id URL_OR_ID
            Zenodo record ID, URL, DOI, or community-request URL.
            Overrides --jira-ticket and config.yml sources.
    --jira-ticket KEY
            Jira issue key (e.g. AEAREP-8983).  Used only when
            --zenodo-id is not given.
    --print-id
            Print the resolved output directory name (zenodo-NNNNN) to
            stdout as the last line of output.  Use in pipelines:
              zenodo_dir=$(python3.12 tools/download_zenodo.py ... --print-id)
    --dry-run
            Pass --dry-run to the selected download script (no files saved).
    --sandbox
            Use sandbox.zenodo.org.

Environment Variables:
    JIRA_USERNAME, JIRA_API_KEY  - Required when --jira-ticket is used
    ZENODO_ACCESS_TOKEN          - Required for private/draft downloads
    CI                           - Set in CI environments

Exit codes:
    0 - Success
    1 - Error
    2 - Not a Zenodo deposit (URL from Jira points elsewhere); caller should
        skip Zenodo and try another downloader
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


# ── URL classification ────────────────────────────────────────────────────────

_REQUEST_RE = re.compile(
    r'zenodo\.org/communities/[^/]+/requests/([0-9a-f-]{36})',
    re.IGNORECASE,
)
_DEPOSIT_RE = re.compile(r'zenodo\.org/(?:deposit/|deposits/)(\d+)', re.IGNORECASE)
_RECORD_RE  = re.compile(r'zenodo\.org/(?:records?/)(\d+)', re.IGNORECASE)
_DOI_RE     = re.compile(r'zenodo\.(\d+)', re.IGNORECASE)
_BARE_RE    = re.compile(r'^\d+$')


def classify_url(raw: str):
    """
    Determine Zenodo URL type and extract the canonical identifier.

    Returns:
        (kind, identifier) where kind is 'request', 'draft', or 'public'
        and identifier is the UUID (for request) or numeric record ID.

    Raises:
        SystemExit(1) if the input does not look like a Zenodo URL/ID.
    """
    raw = raw.strip().rstrip('/')

    if not raw:
        print("ERROR: Empty Zenodo identifier.", file=sys.stderr)
        sys.exit(1)

    if 'zenodo.org' not in raw.lower() and not _DOI_RE.search(raw) and not _BARE_RE.match(raw):
        print(f"ERROR: Does not appear to be a Zenodo URL or ID: {raw!r}", file=sys.stderr)
        sys.exit(1)

    m = _REQUEST_RE.search(raw)
    if m:
        return ('request', m.group(1))   # UUID

    m = _DEPOSIT_RE.search(raw)
    if m:
        return ('draft', m.group(1))

    m = _RECORD_RE.search(raw)
    if m:
        return ('public', m.group(1))

    m = _DOI_RE.search(raw)
    if m:
        return ('public', m.group(1))

    if _BARE_RE.match(raw):
        return ('public', raw)           # bare ID → assume public

    print(f"ERROR: Cannot parse Zenodo identifier: {raw!r}", file=sys.stderr)
    sys.exit(1)


# ── Jira lookup ───────────────────────────────────────────────────────────────

def get_replication_url_from_jira(issue_key: str) -> str:
    """
    Return the 'Replication package URL' field from the given Jira issue.
    Empty string if not set.
    """
    try:
        result = subprocess.run(
            [sys.executable, str(_script_dir() / 'jira_get_info.py'), issue_key.upper(), 'replicationurl'],
            capture_output=True, text=True, check=False,
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Warning: Jira lookup failed: {e}", file=sys.stderr)
        return ""


# ── Dispatch ──────────────────────────────────────────────────────────────────

def _script_dir() -> Path:
    return Path(__file__).parent


def run_public(record_id: str, extra_args: list) -> int:
    cmd = [sys.executable, str(_script_dir() / 'download_zenodo_public.py')] + extra_args + [record_id]
    return subprocess.run(cmd, check=False).returncode


def run_draft(identifier: str, extra_args: list) -> int:
    """identifier is a numeric record ID or a full request URL."""
    cmd = [sys.executable, str(_script_dir() / 'download_zenodo_draft.py')] + extra_args + [identifier]
    return subprocess.run(cmd, check=False).returncode


def record_id_from_request(request_uuid: str, sandbox: bool) -> str:
    """
    Resolve a community-request UUID to a numeric record ID by importing
    resolve_request_to_record_id from download_zenodo_draft.

    Returns the record ID string, or empty string if resolution fails.
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'download_zenodo_draft',
            _script_dir() / 'download_zenodo_draft.py',
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        access_token = mod.get_access_token()
        if not access_token:
            return ''
        return mod.resolve_request_to_record_id(request_uuid, access_token, sandbox)
    except Exception:
        return ''


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Route Zenodo downloads to the appropriate script',
    )
    parser.add_argument('--zenodo-id', default='',
                        help='Zenodo record ID, URL, DOI, or community request URL')
    parser.add_argument('--jira-ticket', default='',
                        help='Jira ticket key; used to fetch replication URL when --zenodo-id is absent')
    parser.add_argument('--print-id', action='store_true',
                        help='Print the resolved zenodo-NNNNN directory name to stdout')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run — list files only, no download')
    parser.add_argument('--sandbox', action='store_true',
                        help='Use sandbox.zenodo.org')
    args = parser.parse_args()

    raw_id = args.zenodo_id.strip()

    # ── Resolve identifier ────────────────────────────────────────────────────
    if not raw_id:
        if not args.jira_ticket:
            print("ERROR: Provide --zenodo-id or --jira-ticket.", file=sys.stderr)
            sys.exit(1)
        print(f"Querying Jira {args.jira_ticket.upper()} for Replication package URL ...")
        raw_id = get_replication_url_from_jira(args.jira_ticket)
        if not raw_id:
            print(
                f"ERROR: No Replication package URL in Jira ticket {args.jira_ticket}.",
                file=sys.stderr,
            )
            sys.exit(1)
        if 'zenodo' not in raw_id.lower():
            print(
                f"INFO: Replication URL is not a Zenodo URL: {raw_id}",
                file=sys.stderr,
            )
            sys.exit(2)
        print(f"Replication URL from Jira: {raw_id}")

    # ── Classify ──────────────────────────────────────────────────────────────
    kind, identifier = classify_url(raw_id)
    print(f"Zenodo URL type : {kind}")
    print(f"Identifier      : {identifier}")

    # ── Build extra flags ─────────────────────────────────────────────────────
    extra: list = []
    if args.dry_run:
        extra.append('--dry-run')
    if args.sandbox:
        extra.append('--sandbox')

    # ── Dispatch ──────────────────────────────────────────────────────────────
    if kind == 'public':
        record_id = identifier
        exit_code = run_public(record_id, extra)
    else:
        # 'draft' or 'request'
        # Pass the full URL so download_zenodo_draft.py can resolve request URLs
        url_or_id = raw_id if kind == 'request' else identifier
        if kind == 'request':
            # Pre-resolve UUID to get record_id for --print-id
            # Falls back to '' if resolution fails (token unavailable etc.)
            record_id = record_id_from_request(identifier, args.sandbox)
        else:
            record_id = identifier
        exit_code = run_draft(url_or_id, extra)

    # ── Print resolved directory name (for pipeline capture) ─────────────────
    if args.print_id and record_id:
        print(f"zenodo-{record_id}")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
