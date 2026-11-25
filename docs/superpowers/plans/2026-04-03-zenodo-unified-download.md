# Zenodo Unified Download Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the public Zenodo download script to Python, sync both Zenodo download scripts in terms of concepts and output, create a routing orchestrator, and integrate it into the populate pipelines.

**Architecture:** Three-script model — `download_zenodo_public.py` (no auth, uses `zenodo_get`), `download_zenodo_draft.py` (auth required, handles deposits and community requests), and `download_zenodo.py` (orchestrator that parses any Zenodo URL/ID/DOI, queries Jira when no override given, and routes to the appropriate downloader). The orchestrator replaces the direct `ZenodoID` handling in both populate pipelines.

**Tech Stack:** Python 3.12, `requests`, `zenodo_get`, `argparse`, `subprocess`, Bitbucket Pipelines YAML, Zenodo REST API (InvenioRDM), Jira REST API (via `jira_get_info.py`).

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `tools/download_zenodo_public.py` | Pure-Python public-record downloader (replaces shell wrapper); generates manifests |
| Modify | `tools/download_zenodo_draft.py` | Add community-request URL support; sync manifest/metadata output with public script |
| Create | `tools/download_zenodo.py` | Orchestrator: parse URL/ID, query Jira, route to correct downloader, print `zenodo-NNNN` |
| Modify | `tools/download_from_jira_url.py` | Switch Zenodo public call from `bash download_zenodo_public.sh` to `python3.12 download_zenodo_public.py` |
| Modify | `bitbucket-pipelines.yml` | Both populate pipelines: replace direct `download_zenodo_draft.py $ZenodoID` with orchestrator; update `projectID` determination |
| Modify | `docs/96-90-download_zenodo_public.md` | Update to reflect Python script |
| Modify | `docs/96-90-download_zenodo_draft.md` | Update to reflect request URL support |
| Create | `docs/96-90-download_zenodo.md` | Orchestrator documentation |

The shell script `tools/download_zenodo_public.sh` is retained but deprecated in favour of the Python script. It is not deleted since it may be called from outside this repository.

---

## Task 1: Create Feature Branch

**Files:** (git only)

- [ ] **Step 1: Create and switch to feature branch**

```bash
git checkout -b feature/zenodo-unified-download development
```

- [ ] **Step 2: Verify branch**

Run: `git branch --show-current`
Expected output: `feature/zenodo-unified-download`

---

## Task 2: Write `tools/download_zenodo_public.py`

This replaces the shell wrapper. It must:
- Accept the same input formats (numeric ID, full URL, DOI)
- Produce identical directory naming: `zenodo-{record_id}/`
- Generate `generated/manifest.zenodo-{record_id}.{DATE}.sha256`, `.md5`, and `metadata.zenodo-{record_id}.txt` (matching `download_zenodo_draft.py`)
- Support `--dry-run`, `--output`, `--sandbox` options
- Suppress progress bar in CI (`CI` env var)
- Git-add output in CI

**Files:**
- Create: `tools/download_zenodo_public.py`
- Test: manual smoke test against a known public record

- [ ] **Step 1: Write the failing smoke test**

```bash
# From repo root — record 10848594 is small and publicly accessible
python3.12 tools/download_zenodo_public.py --dry-run 10848594
```
Expected (before script exists): `python3.12: can't open file 'tools/download_zenodo_public.py': [Errno 2] No such file or directory`

- [ ] **Step 2: Create `tools/download_zenodo_public.py`**

```python
#!/usr/bin/env python3
"""
Download files from a public Zenodo record.

This script downloads all files from a published Zenodo record using the
zenodo_get Python module. It generates manifests and metadata files in the
same format as download_zenodo_draft.py for consistency.

Usage:
    python3 tools/download_zenodo_public.py RECORD_ID_OR_URL
    python3 tools/download_zenodo_public.py --dry-run RECORD_ID_OR_URL

Arguments:
    record_id   Zenodo record identifier. Accepts:
                - Numeric record ID:       12345678
                - Full Zenodo URL:         https://zenodo.org/records/12345678
                - Legacy URL:              https://zenodo.org/record/12345678
                - Zenodo DOI:              10.5281/zenodo.12345678
                - DOI URL:                 https://doi.org/10.5281/zenodo.12345678

Options:
    --output DIR     Parent directory for download (default: current directory)
    --dry-run        List files that would be downloaded without downloading
    --sandbox        Use sandbox.zenodo.org instead of zenodo.org

Environment Variables:
    CI - When set, suppresses progress bar and auto-commits downloaded files

Output:
    Downloads to: zenodo-{record_id}/
    Manifests:    generated/manifest.zenodo-{record_id}.{DATE}.sha256
                  generated/manifest.zenodo-{record_id}.{DATE}.md5
    Metadata:     generated/metadata.zenodo-{record_id}.txt

Exit codes:
    0 - Success
    1 - Download error
    2 - Bad arguments or existing directory
"""

import argparse
import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ZENODO_API_BASE = "https://zenodo.org/api"
SANDBOX_API_BASE = "https://sandbox.zenodo.org/api"


def extract_record_id(raw: str) -> str:
    """
    Extract numeric record ID from various input formats.

    Accepts:
      - Bare numeric ID:      "12345678"
      - zenodo.org URL:       "https://zenodo.org/records/12345678"
      - Legacy URL:           "https://zenodo.org/record/12345678"
      - DOI string:           "10.5281/zenodo.12345678"
      - DOI URL:              "https://doi.org/10.5281/zenodo.12345678"

    Returns:
        Numeric record ID as string.

    Raises:
        SystemExit(2) if ID cannot be determined.
    """
    raw = raw.strip().rstrip('/')

    # Bare number
    if re.fullmatch(r'\d+', raw):
        return raw

    # zenodo.NNNNN pattern (DOI or URL)
    m = re.search(r'zenodo\.(\d+)', raw)
    if m:
        return m.group(1)

    # /records/NNNNN or /record/NNNNN or /deposit/NNNNN
    m = re.search(r'/(?:records?|deposit)/(\d+)', raw)
    if m:
        return m.group(1)

    # Last numeric segment as fallback
    m = re.search(r'/(\d+)$', raw)
    if m:
        return m.group(1)

    print(f"ERROR: Cannot extract Zenodo record ID from: {raw!r}", file=sys.stderr)
    print("Expected formats:", file=sys.stderr)
    print("  12345678", file=sys.stderr)
    print("  https://zenodo.org/records/12345678", file=sys.stderr)
    print("  10.5281/zenodo.12345678", file=sys.stderr)
    sys.exit(2)


def calculate_checksum(filepath: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def save_manifests(output_dir: Path) -> None:
    """
    Walk output_dir and write SHA-256, MD5, and metadata manifests to
    generated/ using the same naming convention as download_zenodo_draft.py.
    """
    generated = Path("generated")
    generated.mkdir(exist_ok=True)

    dir_name = output_dir.name
    date_str = datetime.now().strftime("%Y-%m-%d")
    sha256_file = generated / f"manifest.{dir_name}.{date_str}.sha256"
    md5_file    = generated / f"manifest.{dir_name}.{date_str}.md5"
    meta_file   = generated / f"metadata.{dir_name}.txt"

    sha256_lines = []
    md5_lines    = []
    meta_lines   = ["filename,bytes"]

    for path in sorted(output_dir.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(output_dir)
        size = path.stat().st_size
        sha256_lines.append(f"{calculate_checksum(path, 'sha256')}  ./{rel}")
        md5_lines.append(f"{calculate_checksum(path, 'md5')}  ./{rel}")
        meta_lines.append(f"./{rel},{size}")

    sha256_file.write_text('\n'.join(sorted(sha256_lines)) + '\n')
    md5_file.write_text('\n'.join(sorted(md5_lines)) + '\n')
    meta_file.write_text('\n'.join(meta_lines) + '\n')

    print(f"Manifests written to {sha256_file}, {md5_file}, {meta_file}")


def list_files_dry_run(record_id: str, sandbox: bool) -> None:
    """Fetch metadata and print file list without downloading."""
    import requests
    base = SANDBOX_API_BASE if sandbox else ZENODO_API_BASE
    url = f"{base}/records/{record_id}"
    resp = requests.get(url)
    if resp.status_code == 404:
        print(f"ERROR: Record {record_id} not found.", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    data = resp.json()
    files = data.get('files', [])
    if not files:
        print("No files found in this record.")
        return
    print(f"Record {record_id}: {len(files)} file(s)")
    for i, f in enumerate(files, 1):
        name = f.get('key', f.get('filename', '?'))
        size = f.get('size', f.get('filesize', '?'))
        print(f"  {i:3}. {name}  ({size} bytes)")
    print("\nDry run complete. No files downloaded.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Download files from a public Zenodo record',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'record_id',
        help='Zenodo record ID, URL, or DOI',
    )
    parser.add_argument(
        '--output', default='.',
        help='Parent directory for download (default: current directory)',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='List files without downloading',
    )
    parser.add_argument(
        '--sandbox', action='store_true',
        help='Use sandbox.zenodo.org',
    )
    args = parser.parse_args()

    record_id  = extract_record_id(args.record_id)
    output_dir = Path(args.output) / f"zenodo-{record_id}"

    print(f"Zenodo record ID : {record_id}")
    print(f"Output directory : {output_dir}")

    if args.dry_run:
        list_files_dry_run(record_id, args.sandbox)
        return

    if output_dir.exists():
        print(
            f"ERROR: {output_dir} already exists. Remove it before re-downloading.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Use zenodo_get_ci wrapper which handles CI progress suppression
    import subprocess
    python = sys.executable
    cmd = [python, 'tools/zenodo_get_ci.py', f'--output-dir={output_dir}']
    if args.sandbox:
        cmd.append('--sandbox')
    cmd.append(record_id)

    print(f"Downloading to {output_dir} ...")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print("ERROR: Download failed.", file=sys.stderr)
        sys.exit(1)

    print("Download complete. Generating manifests ...")
    save_manifests(output_dir)

    if os.getenv("CI"):
        os.system(f"git add -v {output_dir} generated/")
        os.system(
            f"git commit -m '[skip ci] Add files from Zenodo public record {record_id}'"
            f" {output_dir} generated/"
        )
    else:
        print(f"Tip: run 'git add {output_dir} generated/' to stage the download.")

    print(f"Done. Files in {output_dir}")


if __name__ == '__main__':
    main()
```

- [ ] **Step 3: Make script executable**

```bash
chmod +x tools/download_zenodo_public.py
```

- [ ] **Step 4: Run dry-run smoke test**

```bash
python3.12 tools/download_zenodo_public.py --dry-run 10848594
```
Expected: file listing from record 10848594, no files downloaded, exit 0.

- [ ] **Step 5: Run a real download into a temp dir**

```bash
cd /tmp && python3.12 /path/to/tools/download_zenodo_public.py --output /tmp/test-zenodo-dl 10848594
ls /tmp/test-zenodo-dl/zenodo-10848594/
ls /tmp/test-zenodo-dl/generated/
```
Expected: files in `zenodo-10848594/`, manifest files in `generated/`.

- [ ] **Step 6: Clean up temp dir**

```bash
rm -rf /tmp/test-zenodo-dl
```

- [ ] **Step 7: Commit**

```bash
git add tools/download_zenodo_public.py
git commit -m "feat: convert download_zenodo_public to pure Python with manifest generation"
```

---

## Task 3: Update `tools/download_zenodo_draft.py` — Add Request URL Support

The private download script must understand community-request URLs of the form:
`https://zenodo.org/communities/aeajournals/requests/{uuid}`

For such URLs:
1. Call `GET https://zenodo.org/api/requests/{uuid}` with the Zenodo access token.
2. Extract the deposit/record ID from the response (field path: `topic.deposit.id` or similar — see step notes).
3. Use that ID for the `zenodo-{record_id}` directory name.
4. Proceed with the existing deposit download logic.

**Files:**
- Modify: `tools/download_zenodo_draft.py` (two new functions + updated `main()` argument parsing)

- [ ] **Step 1: Write failing test — request URL parsing**

Add this temporary test invocation (replace `<uuid>` with the example UUID):
```bash
python3.12 -c "
from tools.download_zenodo_draft import extract_record_id_from_request_url
result = extract_record_id_from_request_url(
    'https://zenodo.org/communities/aeajournals/requests/61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665',
    access_token=None
)
print(result)
"
```
Expected (before change): `AttributeError: module ... has no attribute 'extract_record_id_from_request_url'`

- [ ] **Step 2: Add request UUID extraction to `download_zenodo_draft.py`**

Add the following two functions immediately after the `get_access_token` function (before `main()`):

```python
REQUEST_URL_PATTERN = re.compile(
    r'zenodo\.org/communities/[^/]+/requests/([0-9a-f-]{36})',
    re.IGNORECASE,
)


def is_request_url(url: str) -> bool:
    """Return True if url is a Zenodo community-request URL."""
    return bool(REQUEST_URL_PATTERN.search(url))


def resolve_request_to_record_id(request_uuid: str, access_token: str, sandbox: bool = False) -> str:
    """
    Call the Zenodo requests API to find the record/deposit ID associated
    with the given community request UUID.

    The InvenioRDM requests endpoint returns JSON with the deposit linked
    under topic.  We inspect several possible paths:

        data["topic"]["deposit"]["id"]          # most common
        data["topic"]["record"]["id"]           # published record
        data["links"]["topic"]                  # URL containing the ID

    Returns:
        Numeric record ID as a string.

    Raises:
        SystemExit(1) on API error or if the ID cannot be resolved.
    """
    import re as _re
    base_url = SANDBOX_API_BASE if sandbox else ZENODO_API_BASE
    url = f"{base_url}/requests/{request_uuid}"
    headers = {'Authorization': f'Bearer {access_token}'}

    print(f"Resolving community request {request_uuid} ...")
    resp = requests.get(url, headers=headers)

    if resp.status_code == 401:
        print("ERROR: Unauthorized. Check your Zenodo access token.", file=sys.stderr)
        sys.exit(1)
    if resp.status_code == 404:
        print(f"ERROR: Request {request_uuid} not found.", file=sys.stderr)
        sys.exit(1)
    if resp.status_code != 200:
        print(f"ERROR: HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()

    # Try topic.deposit.id or topic.record.id first
    topic = data.get('topic', {})
    for key in ('deposit', 'record'):
        if key in topic:
            record_id = str(topic[key].get('id', ''))
            if record_id:
                print(f"Resolved request → record ID: {record_id}")
                return record_id

    # Fallback: extract from links.topic URL
    topic_link = data.get('links', {}).get('topic', '')
    m = _re.search(r'/(\d+)/?$', topic_link)
    if m:
        record_id = m.group(1)
        print(f"Resolved request → record ID (from link): {record_id}")
        return record_id

    print(f"ERROR: Cannot resolve record ID from request response.", file=sys.stderr)
    print(f"Response JSON: {data}", file=sys.stderr)
    sys.exit(1)
```

Also add `import re` near the top of the file if not already present (it is not — add after `from urllib.parse import urlparse`):
```python
import re
```

- [ ] **Step 3: Update `main()` in `download_zenodo_draft.py` — handle request URLs**

Replace the record_id cleaning block in `main()`:

```python
    # Old block to replace:
    # Clean record ID (remove URL parts if full URL provided)
    record_id = args.record_id
    if 'zenodo.org' in record_id:
        # Extract ID from URL like https://zenodo.org/deposit/123456 or https://zenodo.org/record/123456
        parts = record_id.split('/')
        record_id = parts[-1]
```

With:

```python
    record_id = args.record_id

    # Resolve community request URLs first (need auth)
    if is_request_url(record_id):
        if not access_token:
            print("ERROR: A Zenodo access token is required to resolve community requests.", file=sys.stderr)
            sys.exit(1)
        m = REQUEST_URL_PATTERN.search(record_id)
        request_uuid = m.group(1)
        record_id = resolve_request_to_record_id(request_uuid, access_token, args.sandbox)
    elif 'zenodo.org' in record_id:
        # Strip to bare numeric ID from deposit/record URL
        parts = record_id.strip('/').split('/')
        record_id = parts[-1]
```

- [ ] **Step 4: Verify dry-run still works for numeric IDs**

```bash
python3.12 tools/download_zenodo_draft.py --dry-run --access-token dummy 12345678
```
Expected: error about unauthorized (401) — proving the code path reaches the API call correctly without crashing on ID extraction.

- [ ] **Step 5: Commit**

```bash
git add tools/download_zenodo_draft.py
git commit -m "feat: add community request URL support to download_zenodo_draft"
```

---

## Task 4: Sync Manifest Output Between the Two Scripts

Both scripts must produce identical `generated/` output structure. After Tasks 2 and 3, verify and patch any differences.

**Files:**
- Compare: `tools/download_zenodo_public.py` vs `tools/download_zenodo_draft.py`

- [ ] **Step 1: Verify manifest naming convention matches**

Run (from repo root, with a completed draft download in `zenodo-NNNNN/`):
```bash
ls generated/manifest.zenodo-*
ls generated/metadata.zenodo-*
```
Both scripts must produce:
- `generated/manifest.zenodo-{record_id}.{YYYY-MM-DD}.sha256`
- `generated/manifest.zenodo-{record_id}.{YYYY-MM-DD}.md5`
- `generated/metadata.zenodo-{record_id}.txt`

- [ ] **Step 2: Verify metadata file format matches**

```bash
head -2 generated/metadata.zenodo-*.txt
```
Expected header line: `filename,bytes`
Expected data lines: `./filename.ext,1234567`

Both scripts must write this exact format.

- [ ] **Step 3: If any discrepancy found, patch the offending script**

(Edit the script whose output does not match and re-run the verification.)

- [ ] **Step 4: Commit if any patches were needed**

```bash
git add tools/download_zenodo_public.py tools/download_zenodo_draft.py
git commit -m "fix: sync manifest/metadata output format between public and draft Zenodo scripts"
```

---

## Task 5: Create `tools/download_zenodo.py` — Orchestrator

This script is the single entry point for all Zenodo downloads in the pipeline.

**Routing logic:**
- URL with `/communities/.../requests/` → **draft/private** (request URL)
- URL with `/deposit/` → **draft/private**
- Everything else (numeric ID, `/records/`, `/record/`, DOI) → **public**

When `--zenodo-id` is not supplied:
1. Require `--jira-ticket`
2. Query `jira_get_info.py TICKET replicationurl`
3. Confirm the URL is a Zenodo URL; abort otherwise

`--print-id` causes the script to print `zenodo-{record_id}` to stdout on the last line (for capture by the pipeline).

**Files:**
- Create: `tools/download_zenodo.py`

- [ ] **Step 1: Write failing test**

```bash
python3.12 tools/download_zenodo.py --help
```
Expected: `No such file or directory`

- [ ] **Step 2: Create `tools/download_zenodo.py`**

```python
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

    if 'zenodo' not in raw.lower() and not _BARE_RE.match(raw):
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
            ['python3.12', 'tools/jira_get_info.py', issue_key.upper(), 'replicationurl'],
            capture_output=True, text=True, check=False,
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Warning: Jira lookup failed: {e}", file=sys.stderr)
        return ""


# ── Dispatch ──────────────────────────────────────────────────────────────────

def run_public(record_id: str, extra_args: list) -> int:
    cmd = ['python3.12', 'tools/download_zenodo_public.py'] + extra_args + [record_id]
    return subprocess.run(cmd, check=False).returncode


def run_draft(identifier: str, extra_args: list) -> int:
    """identifier is a numeric record ID or a full request URL."""
    cmd = ['python3.12', 'tools/download_zenodo_draft.py'] + extra_args + [identifier]
    return subprocess.run(cmd, check=False).returncode


def record_id_from_draft(identifier: str, sandbox: bool) -> str:
    """
    For a request UUID, we can't know the numeric record ID until the draft
    script resolves it.  This helper calls resolve_request_to_record_id
    inline so we can construct the output dir name for --print-id.
    """
    if re.fullmatch(r'[0-9a-f-]{36}', identifier):
        # It's a UUID; need to resolve via API
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from download_zenodo_draft import resolve_request_to_record_id, get_access_token  # noqa
            token = get_access_token()
            if token:
                return resolve_request_to_record_id(identifier, token, sandbox)
        except Exception:
            pass
        # Fallback: can't determine without running draft script
        return ""
    return identifier   # already a numeric ID


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

    # ── Build extra flags ────────────────────────────────────────────────────
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
        # Pass the full URL (or numeric ID) so download_zenodo_draft.py can resolve it
        url_or_id = raw_id if kind == 'request' else identifier
        record_id = record_id_from_draft(identifier, args.sandbox) or identifier
        exit_code = run_draft(url_or_id, extra)

    # ── Print resolved directory name (for pipeline capture) ─────────────────
    if args.print_id:
        if record_id:
            print(f"zenodo-{record_id}")
        else:
            print("", file=sys.stderr)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
```

- [ ] **Step 3: Make executable**

```bash
chmod +x tools/download_zenodo.py
```

- [ ] **Step 4: Run help smoke test**

```bash
python3.12 tools/download_zenodo.py --help
```
Expected: help text listing `--zenodo-id`, `--jira-ticket`, `--print-id`, `--dry-run`, `--sandbox`.

- [ ] **Step 5: Test URL classification**

```bash
python3.12 - <<'EOF'
import sys; sys.path.insert(0, 'tools')
# Rewrite so module is importable without __main__ guard
import importlib.util, types
spec = importlib.util.spec_from_file_location("dz", "tools/download_zenodo.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

cases = [
    ("10848594",                                                              ("public", "10848594")),
    ("https://zenodo.org/records/10848594",                                   ("public", "10848594")),
    ("https://doi.org/10.5281/zenodo.10848594",                               ("public", "10848594")),
    ("10.5281/zenodo.10848594",                                               ("public", "10848594")),
    ("https://zenodo.org/deposit/10848594",                                   ("draft",  "10848594")),
    ("https://zenodo.org/communities/aeajournals/requests/61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665",
                                                                              ("request","61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665")),
]
ok = True
for inp, expected in cases:
    got = m.classify_url(inp)
    status = "OK" if got == expected else "FAIL"
    if got != expected:
        ok = False
    print(f"{status}: {inp!r} -> {got!r}  (expected {expected!r})")
sys.exit(0 if ok else 1)
EOF
```
Expected: all lines say `OK`, exit 0.

- [ ] **Step 6: Dry-run test through orchestrator**

```bash
python3.12 tools/download_zenodo.py --zenodo-id 10848594 --dry-run
```
Expected: delegates to `download_zenodo_public.py --dry-run 10848594`, prints file listing, no download, exit 0.

- [ ] **Step 7: Commit**

```bash
git add tools/download_zenodo.py
git commit -m "feat: add download_zenodo.py orchestrator routing public/private Zenodo downloads"
```

---

## Task 6: Update `tools/download_from_jira_url.py` — Use Python Instead of Bash for Public

The `download_zenodo_public` call in this existing script must use the Python script.

**Files:**
- Modify: `tools/download_from_jira_url.py:218-232`

- [ ] **Step 1: Identify the call site**

In `tools/download_from_jira_url.py`, find `download_zenodo_public`:
```python
def download_zenodo_public(record_id):
    ...
    cmd = ['bash', 'tools/download_zenodo_public.sh', record_id]
```

- [ ] **Step 2: Replace with Python call**

Replace the function body:
```python
def download_zenodo_public(record_id):
    """
    Download from public Zenodo record using download_zenodo_public.py.
    """
    print(f"Downloading from Zenodo public record: {record_id}")
    cmd = ['python3.12', 'tools/download_zenodo_public.py', record_id]
    result = subprocess.run(cmd, check=False)
    return result.returncode
```

- [ ] **Step 3: Verify the function docstring update**

The function at line ~218 in the file should now reference `.py` not `.sh`.

- [ ] **Step 4: Commit**

```bash
git add tools/download_from_jira_url.py
git commit -m "fix: use download_zenodo_public.py instead of shell script in download_from_jira_url"
```

---

## Task 7: Update `bitbucket-pipelines.yml` — Both Populate Pipelines

Two pipelines require changes:
1. `1-populate-from-icpsr` (standard, starts ~line 36)
2. `w-big-populate-from-icpsr` (large, starts ~line 426)

**Changes per pipeline:**
- `ZenodoID` variable: keep, update description comment to clarify it accepts URL, DOI, or ID
- Replace the direct `download_zenodo_draft.py $ZenodoID` call with the orchestrator
- Update `projectID` to capture the orchestrator's `--print-id` output instead of constructing `zenodo-$ZenodoID`

**Files:**
- Modify: `bitbucket-pipelines.yml`

- [ ] **Step 1: Update `1-populate-from-icpsr` — ZenodoID variable comment**

In the variables section of `1-populate-from-icpsr`, find:
```yaml
          - name: ZenodoID
```
Replace with:
```yaml
          - name: ZenodoID
            # Accepts: numeric ID, full URL, DOI, or community request URL.
            # Leave blank if jiraticket is set (orchestrator will query Jira).
```

- [ ] **Step 2: Update `1-populate-from-icpsr` — download and projectID lines**

Find the block (approximately lines 87–101):
```yaml
            - if [ -z $openICPSRID ]; then openICPSRID=$openicpsr; fi
            - if [ -z $ZenodoID ]; then ZenodoID=$zenodo; fi
            - projectID="${openICPSRID}"
            - projectID="${projectID:-zenodo-$ZenodoID}"
            - if [ -z "$jiraticket" ] && [ -n "${openICPSRID:-}" ]; then jiraticket=$(python3 tools/jira_find_task_by_icpsr.py "$openICPSRID" 2>/dev/null || true); else echo "Jira ticket not set"; fi
            - echo "Using Jira case $jiraticket"
            - ./tools/update_config.sh
            - ./automations/70_publish_comment.sh 1-populate-from-icpsr started
            - if [ -d $projectID ]; then \rm -rf $projectID; fi
            - if [ ! -z $openICPSRID ]; then python3 tools/download_openicpsr-private.py $openICPSRID; fi
            - if [ ! -z $ZenodoID ]; then python3 tools/download_zenodo_draft.py $ZenodoID; fi
```

Replace with:
```yaml
            - if [ -z $openICPSRID ]; then openICPSRID=$openicpsr; fi
            - if [ -z $ZenodoID ]; then ZenodoID=$zenodo; fi
            - projectID="${openICPSRID}"
            - if [ -z "$jiraticket" ] && [ -n "${openICPSRID:-}" ]; then jiraticket=$(python3.12 tools/jira_find_task_by_icpsr.py "$openICPSRID" 2>/dev/null || true); else echo "Jira ticket not set"; fi
            - echo "Using Jira case $jiraticket"
            - ./tools/update_config.sh
            - ./automations/70_publish_comment.sh 1-populate-from-icpsr started
            - if [ -d "${projectID:-__none__}" ]; then \rm -rf $projectID; fi
            - if [ ! -z $openICPSRID ]; then python3.12 tools/download_openicpsr-private.py $openICPSRID; fi
            - if [ ! -z "$ZenodoID" ] || [ ! -z "$jiraticket" ]; then zenodo_dir=$(python3.12 tools/download_zenodo.py ${ZenodoID:+--zenodo-id "$ZenodoID"} ${jiraticket:+--jira-ticket "$jiraticket"} --print-id 2>&1 | tail -1); fi
            - if [ -z "$projectID" ] && [ ! -z "${zenodo_dir:-}" ]; then projectID="$zenodo_dir"; fi
```

- [ ] **Step 3: Update `1-populate-from-icpsr` — remove now-redundant zip line for zenodo**

Find:
```yaml
            - if [ ! -z $ZenodoID ]; then zip -rp cache/${projectID}.zip $projectID/* ; fi
```
Replace with (the zip is still useful for caching):
```yaml
            - if [ ! -z "${zenodo_dir:-}" ]; then zip -rp cache/${projectID}.zip $projectID/* ; fi
```

- [ ] **Step 4: Apply identical changes to `w-big-populate-from-icpsr`**

Find the equivalent block (around line 443–452):
```yaml
            - if [ -z $openICPSRID ]; then openICPSRID=$openicpsr; fi
            - if [ -z $ZenodoID ]; then ZenodoID=$zenodo; fi
            - projectID="${openICPSRID}"
            - projectID="${projectID:-zenodo-$ZenodoID}"
            - if [ -z "$jiraticket" ] && [ -n "${openICPSRID:-}" ]; then jiraticket=$(python3 tools/jira_find_task_by_icpsr.py "$openICPSRID" 2>/dev/null || true); fi
            - ./tools/update_config.sh
            - ./automations/70_publish_comment.sh w-big-populate-from-icpsr started
            - if [ -d $projectID ]; then \rm -rf $projectID; fi
            - if [ ! -z $openICPSRID ]; then python3 tools/download_openicpsr-private.py $openICPSRID; fi
            - if [ ! -z $ZenodoID ]; then python3 tools/download_zenodo_draft.py $ZenodoID; fi
```

Replace with:
```yaml
            - if [ -z $openICPSRID ]; then openICPSRID=$openicpsr; fi
            - if [ -z $ZenodoID ]; then ZenodoID=$zenodo; fi
            - projectID="${openICPSRID}"
            - if [ -z "$jiraticket" ] && [ -n "${openICPSRID:-}" ]; then jiraticket=$(python3.12 tools/jira_find_task_by_icpsr.py "$openICPSRID" 2>/dev/null || true); fi
            - ./tools/update_config.sh
            - ./automations/70_publish_comment.sh w-big-populate-from-icpsr started
            - if [ -d "${projectID:-__none__}" ]; then \rm -rf $projectID; fi
            - if [ ! -z $openICPSRID ]; then python3.12 tools/download_openicpsr-private.py $openICPSRID; fi
            - if [ ! -z "$ZenodoID" ] || [ ! -z "$jiraticket" ]; then zenodo_dir=$(python3.12 tools/download_zenodo.py ${ZenodoID:+--zenodo-id "$ZenodoID"} ${jiraticket:+--jira-ticket "$jiraticket"} --print-id 2>&1 | tail -1); fi
            - if [ -z "$projectID" ] && [ ! -z "${zenodo_dir:-}" ]; then projectID="$zenodo_dir"; fi
```

- [ ] **Step 5: Also update `w-big-populate-from-icpsr` ZenodoID variable comment**

Find (around line 430):
```yaml
          - name: ZenodoID
```
Replace with:
```yaml
          - name: ZenodoID
            # Accepts: numeric ID, full URL, DOI, or community request URL.
            # Leave blank if jiraticket is set (orchestrator will query Jira).
```

- [ ] **Step 6: Validate YAML is well-formed**

```bash
python3.12 -c "import yaml; yaml.safe_load(open('bitbucket-pipelines.yml'))" && echo "YAML OK"
```
Expected: `YAML OK`

- [ ] **Step 7: Commit**

```bash
git add bitbucket-pipelines.yml
git commit -m "feat: integrate download_zenodo orchestrator into both populate pipelines"
```

---

## Task 8: Update Documentation

**Files:**
- Modify: `docs/96-90-download_zenodo_public.md`
- Modify: `docs/96-90-download_zenodo_draft.md`
- Create:  `docs/96-90-download_zenodo.md`

- [ ] **Step 1: Update `docs/96-90-download_zenodo_public.md`**

Replace the entire file content:

````markdown
(help-download_zenodo_public)=
# download_zenodo_public.py — Download files from public Zenodo records

## Description

Pure-Python script that downloads all files from a published Zenodo record,
then writes SHA-256, MD5, and metadata manifests to `generated/` using the
same format as `download_zenodo_draft.py`.

The legacy shell wrapper `download_zenodo_public.sh` is retained for
backwards compatibility but is deprecated; use the Python script instead.

## Usage

```bash
python3.12 tools/download_zenodo_public.py RECORD_ID_OR_URL
python3.12 tools/download_zenodo_public.py --dry-run RECORD_ID_OR_URL
```

## Arguments

- **RECORD_ID_OR_URL** — Zenodo identifier in any of these forms:
  - Numeric ID: `12345678`
  - Record URL: `https://zenodo.org/records/12345678`
  - Legacy URL: `https://zenodo.org/record/12345678`
  - DOI string: `10.5281/zenodo.12345678`
  - DOI URL:    `https://doi.org/10.5281/zenodo.12345678`

## Options

| Option | Description |
|--------|-------------|
| `--output DIR` | Parent directory (default: `.`) |
| `--dry-run` | List files without downloading |
| `--sandbox` | Use `sandbox.zenodo.org` |

## Output

```
zenodo-12345678/           ← downloaded files
generated/
  manifest.zenodo-12345678.YYYY-MM-DD.sha256
  manifest.zenodo-12345678.YYYY-MM-DD.md5
  metadata.zenodo-12345678.txt
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `CI` | Suppresses progress; auto-commits with `[skip ci]` |

## See Also

- `tools/download_zenodo_draft.py` — for draft or community-review deposits
- `tools/download_zenodo.py` — orchestrator (recommended entry point)
````

- [ ] **Step 2: Update `docs/96-90-download_zenodo_draft.md`**

Add a section describing the new community-request URL support.  Open the file and append (or insert before "See also"):

```markdown
## Community Request URLs

Draft deposits under community review can be addressed using the request URL:

```
https://zenodo.org/communities/<community>/requests/<uuid>
```

The script calls `GET /api/requests/{uuid}` to resolve the deposit record ID,
then proceeds with the normal draft download.  An access token is required.

```bash
python3.12 tools/download_zenodo_draft.py \
  https://zenodo.org/communities/aeajournals/requests/61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665 \
  --access-token $ZENODO_ACCESS_TOKEN
```
```

- [ ] **Step 3: Create `docs/96-90-download_zenodo.md`**

```markdown
(help-download_zenodo)=
# download_zenodo.py — Zenodo download orchestrator

## Description

Single entry point for all Zenodo downloads.  Parses any Zenodo URL, DOI,
or record ID, determines whether the target is a public record or a private
draft/community request, and delegates to the appropriate script.

When no `--zenodo-id` is given, the orchestrator queries the Jira ticket for
the "Replication package URL".

## Usage

```bash
# Explicit ID or URL
python3.12 tools/download_zenodo.py --zenodo-id 10848594
python3.12 tools/download_zenodo.py --zenodo-id https://zenodo.org/records/10848594
python3.12 tools/download_zenodo.py --zenodo-id https://zenodo.org/communities/aeajournals/requests/61cff0cb-b3ca-48aa-bfe6-5b17dc8eb665

# From Jira ticket
python3.12 tools/download_zenodo.py --jira-ticket AEAREP-8983

# In a pipeline (capture directory name)
zenodo_dir=$(python3.12 tools/download_zenodo.py --zenodo-id "$ZenodoID" --print-id 2>&1 | tail -1)
```

## Options

| Option | Description |
|--------|-------------|
| `--zenodo-id URL_OR_ID` | Zenodo record ID, URL, DOI, or community request URL.  Skips Jira lookup. |
| `--jira-ticket KEY` | Jira issue key; used when `--zenodo-id` is absent |
| `--print-id` | Print `zenodo-NNNNN` to stdout (last line) for pipeline capture |
| `--dry-run` | Pass through to the selected download script |
| `--sandbox` | Use `sandbox.zenodo.org` |

## URL Routing

| URL pattern | Script called |
|-------------|--------------|
| `/records/NNNNN`, `/record/NNNNN`, `10.5281/zenodo.NNNNN`, bare ID | `download_zenodo_public.py` |
| `/deposit/NNNNN` | `download_zenodo_draft.py` |
| `/communities/.../requests/{uuid}` | `download_zenodo_draft.py` (resolves UUID → record ID via API) |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `JIRA_USERNAME`, `JIRA_API_KEY` | Required when `--jira-ticket` is used |
| `ZENODO_ACCESS_TOKEN` | Required for draft/private downloads |
| `CI` | Auto-commit behaviour in pipelines |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |
| 2 | Replication URL from Jira is not a Zenodo URL |

## See Also

- `tools/download_zenodo_public.py`
- `tools/download_zenodo_draft.py`
```

- [ ] **Step 4: Commit docs**

```bash
git add docs/96-90-download_zenodo_public.md docs/96-90-download_zenodo_draft.md docs/96-90-download_zenodo.md
git commit -m "docs: update Zenodo download documentation for orchestrator and Python public script"
```

---

## Task 9: Deprecate Shell Script

- [ ] **Step 1: Add deprecation notice to `tools/download_zenodo_public.sh`**

Insert after the shebang line (line 1), replacing the existing first comment line:

```bash
# DEPRECATED: Use tools/download_zenodo_public.py instead.
# This shell wrapper is retained for external callers only.
# It will be removed in a future release.
```

- [ ] **Step 2: Commit**

```bash
git add tools/download_zenodo_public.sh
git commit -m "chore: deprecate download_zenodo_public.sh in favour of Python script"
```

---

## Task 10: Final Verification

- [ ] **Step 1: Run public script dry-run**

```bash
python3.12 tools/download_zenodo_public.py --dry-run https://zenodo.org/records/10848594
```
Expected: file listing for record 10848594, exit 0.

- [ ] **Step 2: Run orchestrator with explicit URL (public)**

```bash
python3.12 tools/download_zenodo.py --zenodo-id https://doi.org/10.5281/zenodo.10848594 --dry-run --print-id
```
Expected: output ends with `zenodo-10848594`, exit 0.

- [ ] **Step 3: Validate YAML still parses**

```bash
python3.12 -c "import yaml; yaml.safe_load(open('bitbucket-pipelines.yml'))" && echo "YAML OK"
```
Expected: `YAML OK`

- [ ] **Step 4: Verify all new Python scripts are importable (no syntax errors)**

```bash
python3.12 -m py_compile tools/download_zenodo_public.py && echo "public OK"
python3.12 -m py_compile tools/download_zenodo_draft.py && echo "draft OK"
python3.12 -m py_compile tools/download_zenodo.py && echo "orchestrator OK"
```
Expected: all three print `OK`.

- [ ] **Step 5: Push feature branch**

```bash
git push -u origin feature/zenodo-unified-download
```

---

## Self-Review Checklist

- [x] **Public download → Python**: Task 2 creates `download_zenodo_public.py` with manifest generation.
- [x] **Private download → request URL support**: Task 3 adds `is_request_url` / `resolve_request_to_record_id` to draft script.
- [x] **Manifest sync**: Task 4 verifies both scripts produce identical `generated/` structure.
- [x] **Orchestrator**: Task 5 creates `download_zenodo.py` with Jira fallback and `--print-id`.
- [x] **Pipeline integration**: Task 7 updates both `1-populate-from-icpsr` and `w-big-populate-from-icpsr`.
- [x] **ZenodoID field**: Updated to accept URL/DOI/ID; comment added; optional override preserved.
- [x] **`download_from_jira_url.py`**: Task 6 switches to Python script.
- [x] **Documentation**: Task 8 updates all three docs.
- [x] **Shell script deprecated**: Task 9.
- [x] **Feature branch**: Task 1 creates `feature/zenodo-unified-download`.
- [x] **No placeholders**: All code blocks contain actual implementation.
- [x] **Type consistency**: `classify_url` returns `(kind, identifier)` tuples used consistently in `main()`.
