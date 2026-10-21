#!/usr/bin/env python3
"""
Download datasets from Dataverse repositories.

Version: 2.0.0

This script downloads all files of a Dataverse dataset (Harvard Dataverse or
any other Dataverse installation), file by file, preserving the dataset's
folder structure. Files are fetched individually rather than as a single
dataset ZIP because Dataverse caps the size of dataset-level ZIP downloads
and silently omits files beyond that cap.

Usage:
    python3 tools/download_dv.py IDENTIFIER [--server_url URL] [--output PATH]
    python3 tools/download_dv.py --doi DOI [--server_url URL] [--output PATH]

Examples:
    # DOI, in any common form
    python3 tools/download_dv.py doi:10.7910/DVN/T81OHQ
    python3 tools/download_dv.py 10.7910/DVN/T81OHQ
    python3 tools/download_dv.py https://doi.org/10.7910/DVN/T81OHQ

    # Dataverse landing page URL (the server is taken from the URL)
    python3 tools/download_dv.py "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/T81OHQ"

    # Legacy form
    python3 tools/download_dv.py --doi "doi:10.7910/DVN/ABC123" --server_url "https://dataverse.example.edu"

    # Using the Jira ticket's "Replication package URL" (pipeline use)
    python3 tools/download_dv.py --jira-ticket AEAREP-9261 --print-id

    # Only print the output directory name (no network access)
    python3 tools/download_dv.py https://doi.org/10.7910/DVN/T81OHQ --dir-name

Server detection:
    --server_url wins if given. Otherwise the host of a Dataverse landing-page
    URL is used, or the DOI is resolved via doi.org to find the hosting
    installation. Falls back to https://dataverse.harvard.edu.

Output Structure:
    Input DOI: doi:10.7910/DVN/ABC123
    Output directory: ./dv-DVN-ABC123/
    Files are saved under their Dataverse folder (directoryLabel). Ingested
    tabular files are downloaded in their original format (e.g. .csv, .dta)
    rather than as Dataverse's .tab export. Each file's checksum is verified.
    Restricted files cannot be downloaded without authentication; they are
    listed and skipped.

Pipeline options:
    --jira-ticket KEY
            When no identifier is given, read the Jira ticket's
            "Replication package URL" and use it if it is a Dataverse deposit.
    --print-id
            Send all progress output to stderr and print only the output
            directory name (dv-...) to stdout on success, e.g.
              dv_dir=$(python3 tools/download_dv.py ... --print-id)
    --dir-name
            Print the output directory name for the identifier and exit,
            without downloading anything.

Exit codes:
    0 - Success
    1 - Error (bad identifier, API error, failed or corrupt downloads)
    2 - Not a Dataverse deposit (only with --jira-ticket and no identifier)

Git Integration:
    In CI environments (CI set, and not --print-id): automatically commits
    the downloaded files. Otherwise suggests manual git operations.

Requirements:
    Python standard library only. --jira-ticket additionally needs
    tools/jira_get_info.py and its Jira credentials.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

__version__ = '2.0.0'

SERVER_URL = 'https://dataverse.harvard.edu'
USER_AGENT = f'AEA-replication-template/download_dv.py {__version__}'

# Identifiers of other repositories the pipeline handles separately; never
# worth a DOI resolution round-trip.
OTHER_REPOSITORIES = ('zenodo', '10.5281/', 'openicpsr', '10.3886/',
                      'reproducibility.worldbank.org', '10.60572/', 'osf.io', '10.17605/')


def parse_identifier(input_str):
    """
    Split a Dataverse identifier into (doi, server_url).

    doi is normalized to '10.xxxx/...' (no 'doi:' prefix); server_url is the
    Dataverse host when the input is a landing-page URL, else None.
    Raises ValueError if no DOI can be found.
    """
    s = urllib.parse.unquote(input_str.strip())
    server = None
    m = re.search(r'persistentId=(?:doi:)?(10\.\d{4,9}/[^&#\s]+)', s, re.IGNORECASE)
    if m:
        doi = m.group(1)
        parsed = urllib.parse.urlparse(s)
        if parsed.scheme and parsed.netloc:
            server = f'{parsed.scheme}://{parsed.netloc}'
    else:
        m = re.search(r'(?:doi\.org/|doi:|^)(10\.\d{4,9}/\S+)$', s, re.IGNORECASE)
        if not m:
            raise ValueError(f"Could not find a DOI in '{input_str}'")
        doi = m.group(1)
    return doi.rstrip('/'), server


def dir_name(doi):
    """Output directory name: dv- plus the last two DOI path components."""
    return 'dv-' + '-'.join(doi.split('/')[-2:])


def http_get(url, allow_redirects=True):
    """GET url; return the response object (caller closes)."""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    if allow_redirects:
        return urllib.request.urlopen(req, timeout=120)
    opener = urllib.request.build_opener(_NoRedirect)
    return opener.open(req, timeout=60)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def resolve_doi_landing(doi):
    """Return the URL doi.org redirects the DOI to, or '' on failure."""
    try:
        with http_get(f'https://doi.org/{doi}', allow_redirects=False) as r:
            return r.headers.get('Location', '')
    except urllib.error.HTTPError as e:
        return e.headers.get('Location', '') if e.code in (301, 302, 303, 307, 308) else ''
    except Exception as e:
        print(f"⚠️  Could not resolve DOI {doi}: {e}")
        return ''


def is_dataverse_url(input_str):
    """
    Return True if the string looks like a Dataverse deposit.

    Obvious Dataverse markers are accepted directly; other DOIs are resolved
    via doi.org and accepted if they land on a Dataverse dataset page.
    """
    s = input_str.lower()
    if any(k in s for k in OTHER_REPOSITORIES):
        return False
    if 'dataverse' in s or 'dataset.xhtml' in s or '/dvn/' in s:
        return True
    try:
        doi, _ = parse_identifier(input_str)
    except ValueError:
        return False
    return 'dataset.xhtml?persistentid=' in resolve_doi_landing(doi).lower()


def find_server(doi, server_from_url):
    """Pick the Dataverse installation hosting the DOI."""
    if server_from_url:
        return server_from_url
    landing = resolve_doi_landing(doi)
    if 'dataset.xhtml' in landing:
        parsed = urllib.parse.urlparse(landing)
        return f'{parsed.scheme}://{parsed.netloc}'
    return SERVER_URL


def get_replication_url_from_jira(issue_key):
    """
    Return the 'Replication package URL' field from the given Jira issue.
    Empty string if not set or if the lookup fails.
    """
    script = Path(__file__).parent / 'jira_get_info.py'
    try:
        result = subprocess.run(
            [sys.executable, str(script), issue_key.upper(), 'replicationurl'],
            capture_output=True, text=True, check=False,
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"⚠️  Jira lookup failed: {e}", file=sys.stderr)
        return ""


def get_dataset(server_url, doi):
    """Return the dataset JSON ('data' element) from the native API."""
    url = f'{server_url}/api/datasets/:persistentId/?persistentId=doi:{doi}'
    with http_get(url) as r:
        info = json.load(r)
    if info.get('status') != 'OK':
        raise RuntimeError(f"Dataverse API returned status {info.get('status')}: {info.get('message', '')}")
    return info['data']


def file_plan(files):
    """
    Turn the dataset's file list into download entries.

    Returns (entries, restricted): entries is a list of dicts with id,
    relpath, url suffix, size and checksum; restricted lists relpaths of
    files that cannot be fetched anonymously.
    """
    entries, restricted = [], []
    for f in files:
        df = f['dataFile']
        original = df.get('originalFileName')
        name = original or df['filename']
        folder = f.get('directoryLabel') or ''
        relpath = os.path.normpath(os.path.join(folder, name))
        if relpath.startswith('..') or os.path.isabs(relpath):
            raise RuntimeError(f"Refusing unsafe file path from Dataverse: {relpath}")
        if f.get('restricted'):
            restricted.append(relpath)
            continue
        checksum = df.get('checksum') or {}
        entries.append({
            'id': df['id'],
            'relpath': relpath,
            'query': '?format=original' if original else '',
            # filesize is of the ingested .tab; originalFileSize of the original
            'size': df.get('originalFileSize') if original else df.get('filesize'),
            'algo': (checksum.get('type') or '').lower().replace('-', ''),
            'checksum': checksum.get('value', ''),
        })
    return entries, restricted


def download_file(server_url, entry, dest_dir):
    """Download one file and verify its checksum. Returns an error string or ''."""
    target = Path(dest_dir) / entry['relpath']
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"{server_url}/api/access/datafile/{entry['id']}{entry['query']}"
    algo = entry['algo'] if entry['algo'] in hashlib.algorithms_available else ''
    h = hashlib.new(algo) if algo else None
    written = 0
    try:
        with http_get(url) as r, open(target, 'wb') as out:
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                written += len(chunk)
                if h:
                    h.update(chunk)
    except Exception as e:
        return f"download failed: {e}"
    if h and entry['checksum'] and h.hexdigest().lower() != entry['checksum'].lower():
        return f"{algo} checksum mismatch"
    if entry['size'] is not None and written != entry['size']:
        return f"size mismatch ({written:,} bytes, expected {entry['size']:,})"
    return ''


def format_bytes(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def main():
    parser = argparse.ArgumentParser(description='Download a Dataverse dataset')
    parser.add_argument('identifier', nargs='?', default='', help='DOI (doi:10.7910/DVN/..., 10.7910/DVN/..., https://doi.org/...) or Dataverse dataset URL')
    parser.add_argument('--doi', default='', help='Same as the positional identifier (kept for compatibility)')
    parser.add_argument('--server_url', '--server-url', default='', help=f'URL of the Dataverse installation (default: detected, else {SERVER_URL})')
    parser.add_argument('--output', default='.', help='Parent directory for the dv-... output directory (default: current directory)')
    parser.add_argument('--jira-ticket', default='', help="Jira ticket key; its 'Replication package URL' is used when no identifier is given")
    parser.add_argument('--print-id', action='store_true', help='Print only the output directory name (dv-...) to stdout; all other output goes to stderr')
    parser.add_argument('--dir-name', action='store_true', help='Print the output directory name for the identifier and exit without downloading')
    parser.add_argument('--dry-run', action='store_true', help='List the files that would be downloaded without downloading them')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    args = parser.parse_args()

    identifier = args.identifier or args.doi

    if args.dir_name:
        try:
            print(dir_name(parse_identifier(identifier)[0]))
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # With --print-id, stdout carries only the directory name for pipeline capture
    real_stdout = sys.stdout
    if args.print_id:
        sys.stdout = sys.stderr

    print(f"Dataverse Download Script - Version {__version__}")

    if not identifier:
        if not args.jira_ticket:
            print("❌ Error: Provide a Dataverse identifier or --jira-ticket.")
            sys.exit(1)
        print(f"🔎 Querying Jira {args.jira_ticket.upper()} for Replication package URL ...")
        identifier = get_replication_url_from_jira(args.jira_ticket)
        if not identifier:
            print(f"ℹ️  No Replication package URL in Jira ticket {args.jira_ticket}.")
            sys.exit(2)
        if not is_dataverse_url(identifier):
            print(f"ℹ️  Replication URL is not a Dataverse deposit: {identifier}")
            sys.exit(2)
        print(f"✅ Replication URL from Jira: {identifier}")

    try:
        doi, server_from_url = parse_identifier(identifier)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    server_url = (args.server_url or find_server(doi, server_from_url)).rstrip('/')
    output_dir = Path(args.output) / dir_name(doi)
    print(f"Dataverse URL:    {server_url}")
    print(f"Dataset DOI:      doi:{doi}")
    print(f"Output directory: {output_dir}")

    try:
        data = get_dataset(server_url, doi)
    except Exception as e:
        print(f"❌ Could not retrieve dataset metadata: {e}")
        sys.exit(1)

    version = data['latestVersion']
    print(f"Version:          {version.get('versionNumber', '?')}.{version.get('versionMinorNumber', '?')} ({version.get('versionState', '?')})")
    try:
        entries, restricted = file_plan(version.get('files', []))
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)
    total = sum(e['size'] or 0 for e in entries)
    print(f"Files:            {len(entries)} to download ({format_bytes(total)}), {len(restricted)} restricted")
    for r in restricted:
        print(f"  🔒 restricted, skipped: {r}")

    if args.dry_run:
        for e in entries:
            print(f"  📄 {e['relpath']} ({format_bytes(e['size'] or 0)})")
        print("\n🔍 Dry run completed. No files were downloaded.")
        if args.print_id:
            print(output_dir.name, file=real_stdout)
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    failed = []
    for i, e in enumerate(entries, 1):
        print(f"[{i}/{len(entries)}] {e['relpath']} ({format_bytes(e['size'] or 0)})")
        err = download_file(server_url, e, output_dir)
        if err:
            print(f"  ❌ {err}")
            failed.append(e['relpath'])

    if failed:
        print(f"\n❌ {len(failed)} of {len(entries)} files failed:")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)

    print(f"\n✅ Downloaded {len(entries)} files ({format_bytes(total)}) to {output_dir}")
    if restricted:
        print(f"⚠️  {len(restricted)} restricted files were not downloaded (see above).")

    if args.print_id:
        print(output_dir.name, file=real_stdout)
    elif os.getenv("CI"):
        # we are on a pipeline/action
        subprocess.run(['git', 'add', '-v', str(output_dir)], check=False)
        subprocess.run(['git', 'commit', '-m', f'[skip ci] Adding files from Dataverse dataset doi:{doi}', str(output_dir)], check=False)
    else:
        print(f"You may want to 'git add' the contents of {output_dir}")


if __name__ == '__main__':
    main()
