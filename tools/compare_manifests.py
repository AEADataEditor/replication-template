#!/usr/bin/env python3

# This script compares two manifest files (SHA256 checksum files) to identify changes.
# It takes a required "newer" file and an optional "older" file as arguments.
# If the "older" file is not provided, it attempts to find a previous manifest file based on the date in the filename.
# The script identifies files that have been added, removed, or changed between the two manifests.

import sys
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict

def find_previous_manifest(current_file):
    # Extract the date from the filename
    match = re.search(r'\.(\d{4}-\d{2}-\d{2})\.sha256$', current_file)
    if not match:
        raise ValueError(f"Filename {current_file} does not contain a valid date.")
    
    current_date = datetime.strptime(match.group(1), '%Y-%m-%d')
    previous_date = current_date - timedelta(days=1)
    previous_file = current_file.replace(match.group(1), previous_date.strftime('%Y-%m-%d'))
    
    if not os.path.exists(previous_file):
        raise FileNotFoundError(f"Previous manifest file {previous_file} not found.")
    
    return previous_file

def read_manifest(file_path):
    files = {}
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split('  ', 1)
            if len(parts) == 2:
                checksum, filepath = parts
                files[filepath] = checksum
    return files

def main():
    if len(sys.argv) < 2:
        print("Usage: compare_manifests.py <newer_file.sha256> [older_file.sha256]")
        sys.exit(1)
    
    newer_file = sys.argv[1]
    if not newer_file.endswith('.sha256'):
        print("Error: The newer file must have a '.sha256' extension.")
        sys.exit(1)
    
    if len(sys.argv) > 2:
        older_file = sys.argv[2]
        if not older_file.endswith('.sha256'):
            print("Error: The older file must have a '.sha256' extension.")
            sys.exit(1)
    else:
        try:
            older_file = find_previous_manifest(newer_file)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    # Ensure the files are correctly ordered by date
    newer_date = re.search(r'\.(\d{4}-\d{2}-\d{2})\.sha256$', newer_file).group(1)
    older_date = re.search(r'\.(\d{4}-\d{2}-\d{2})\.sha256$', older_file).group(1)

    if datetime.strptime(older_date, '%Y-%m-%d') > datetime.strptime(newer_date, '%Y-%m-%d'):
        print("Warning: The older file has a more recent date than the newer file. Swapping terms.")
        newer_file, older_file = older_file, newer_file

    files_newer = read_manifest(newer_file)
    files_older = read_manifest(older_file)

    # Find files that exist in both but have different checksums
    changed = []
    for filepath in sorted(set(files_newer.keys()) & set(files_older.keys())):
        if files_newer[filepath] != files_older[filepath]:
            changed.append(filepath)

    # Find files only in the newer file
    only_in_newer = sorted(set(files_newer.keys()) - set(files_older.keys()))

    # Find files only in the older file
    only_in_older = sorted(set(files_older.keys()) - set(files_newer.keys()))

    print('Files that exist in both manifests but have different checksums:')
    for f in changed:
        print(f'  {f}')

    print('\nFiles only in newer manifest (added):')
    for f in only_in_newer:
        print(f'  {f}')

    print('\nFiles only in older manifest (removed):')
    for f in only_in_older:
        print(f'  {f}')

if __name__ == "__main__":
    main()