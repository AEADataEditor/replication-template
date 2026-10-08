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
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

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
    meta_data_lines = []

    for path in sorted(output_dir.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(output_dir)
        size = path.stat().st_size
        sha256_lines.append(f"{calculate_checksum(path, 'sha256')}  ./{rel}")
        md5_lines.append(f"{calculate_checksum(path, 'md5')}  ./{rel}")
        meta_data_lines.append(f"./{rel},{size}")

    sha256_file.write_text('\n'.join(sorted(sha256_lines)) + '\n')
    md5_file.write_text('\n'.join(sorted(md5_lines)) + '\n')
    meta_file.write_text('\n'.join(["filename,bytes"] + sorted(meta_data_lines)) + '\n')

    print(f"Manifests written to {sha256_file}, {md5_file}, {meta_file}")


def list_files_dry_run(record_id: str, sandbox: bool) -> None:
    """Fetch metadata and print file list without downloading."""
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
    python = sys.executable
    script_dir = Path(__file__).parent
    zenodo_get_ci = script_dir / "zenodo_get_ci.py"
    cmd = [python, str(zenodo_get_ci), f'--output-dir={output_dir}']
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
        subprocess.run(["git", "add", "-v", str(output_dir), "generated/"], check=False)
        subprocess.run(
            [
                "git", "commit",
                "-m", f"[skip ci] Add files from Zenodo public record {record_id}",
                str(output_dir), "generated/",
            ],
            check=False,
        )
    else:
        print(f"Tip: run 'git add {output_dir} generated/' to stage the download.")

    print(f"Done. Files in {output_dir}")


if __name__ == '__main__':
    main()
