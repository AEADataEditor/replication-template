#!/usr/bin/env python3
"""
Compare two SHA256 manifest files and identify overlaps.

This script analyzes two SHA256 checksum files and reports:
1. Filenames that appear in both files
2. Checksums that appear in both files (potential duplicates)
3. Complete records (filename + checksum) that match exactly

Usage: python compare_manifests.py <manifest1> <manifest2>
"""

import sys
import argparse
from pathlib import Path
from collections import defaultdict

def parse_manifest(filepath):
    """
    Parse a SHA256 manifest file and return dictionaries mapping:
    - filenames to checksums
    - checksums to filenames (for finding duplicate content)
    - basenames to full paths (for path-independent comparison)
    """
    file_to_checksum = {}
    checksum_to_files = defaultdict(list)
    basename_to_files = defaultdict(list)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Handle both "checksum filename" and "checksum *filename" formats
                parts = line.split(None, 1)
                if len(parts) != 2:
                    print(f"Warning: Skipping malformed line {line_num} in {filepath}: {line}")
                    continue
                
                checksum, filename = parts
                # Remove leading '*' if present (indicates binary mode)
                if filename.startswith('*'):
                    filename = filename[1:]
                
                file_to_checksum[filename] = checksum
                checksum_to_files[checksum].append(filename)
                
                # Extract basename for path-independent comparison
                basename = Path(filename).name
                basename_to_files[basename].append(filename)
                
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        sys.exit(1)
    
    return file_to_checksum, checksum_to_files, basename_to_files

def compare_manifests(manifest1_path, manifest2_path):
    """Compare two manifest files and report overlaps."""
    
    print(f"Comparing manifests:")
    print()
    
    # Parse both manifests
    files1, checksums1, basenames1 = parse_manifest(manifest1_path)
    files2, checksums2, basenames2 = parse_manifest(manifest2_path)
    
    print(f"- File 1 ({manifest1_path}) contains {len(files1)} entries")
    print(f"- File 2 ({manifest2_path}) contains {len(files2)} entries")
    print()
    
    # Find overlapping basenames (path-independent comparison)
    common_basenames = set(basenames1.keys()) & set(basenames2.keys())
    
    # Find overlapping checksums
    common_checksums = set(checksums1.keys()) & set(checksums2.keys())
    
    # Find exact matches (same basename and same checksum)
    exact_matches = []
    basename_checksum_mismatches = []
    
    for basename in common_basenames:
        # Get all files with this basename from both manifests
        files_in_1 = basenames1[basename]
        files_in_2 = basenames2[basename]
        
        for file1 in files_in_1:
            checksum1 = files1[file1]
            for file2 in files_in_2:
                checksum2 = files2[file2]
                if checksum1 == checksum2:
                    exact_matches.append((basename, file1, file2, checksum1))
                else:
                    basename_checksum_mismatches.append((basename, file1, checksum1, file2, checksum2))
    
    # Report results
    print("📁 BASENAMES THAT APPEAR IN BOTH MANIFESTS:")
    print()
    print(f"Found {len(common_basenames)} common basenames")
    if common_basenames:
        for basename in sorted(common_basenames):
            files_in_1 = basenames1[basename]
            files_in_2 = basenames2[basename]
            print(f"  {basename}")
            print(f"    In manifest 1: {', '.join(files_in_1)}")
            print(f"    In manifest 2: {', '.join(files_in_2)}")
        print()
    
    print("🔍 CHECKSUMS THAT APPEAR IN BOTH MANIFESTS:")
    print()
    print(f"Found {len(common_checksums)} common checksums")
    if common_checksums:
        for checksum in sorted(common_checksums):
            files_in_1 = checksums1[checksum]
            files_in_2 = checksums2[checksum]
            print(f"- {checksum}")
            print(f"  - In manifest 1: {', '.join(files_in_1)}")
            print(f"  - In manifest 2: {', '.join(files_in_2)}")
            print()
    
    print("✅ EXACT MATCHES (same basename and checksum):")
    print()
    print(f"Found {len(exact_matches)} exact matches")
    if exact_matches:
        for basename, file1, file2, checksum in sorted(exact_matches):
            print(f"- {checksum}")
            print(f"  - In manifest 1: {file1}")
            print(f"  - In manifest 2: {file2}")
            print()
    
    print("⚠️  BASENAME MATCHES WITH DIFFERENT CHECKSUMS:")
    print()
    print("*This compares all files with the same name, regardless of path.*")
    print()
    print(f"Found {len(basename_checksum_mismatches)} files with same basename but different checksums")
    if basename_checksum_mismatches:
        for basename, file1, checksum1, file2, checksum2 in sorted(basename_checksum_mismatches):
            print(f"- {basename}")
            print(f"  - Manifest 1: {file1} -> {checksum1}")
            print(f"  - Manifest 2: {file2} -> {checksum2}")
            print()
    
    # Summary statistics
    print()
    print("📊 SUMMARY:")
    print()
    print(f"-  Total files in manifest 1: {len(files1)}")
    print(f"-  Total files in manifest 2: {len(files2)}")
    print(f"-  Common basenames: {len(common_basenames)}")
    print(f"-  Common checksums: {len(common_checksums)}")
    print(f"-  Exact matches: {len(exact_matches)}")
    print(f"-  Same basename, different checksum: {len(basename_checksum_mismatches)}")

def main():
    parser = argparse.ArgumentParser(
        description="Compare two SHA256 manifest files and identify overlaps",
        epilog="Example: python compare_manifests.py manifest-1-sha256sum manifest-2-sha256sum"
    )
    parser.add_argument("manifest1", help="Path to first SHA256 manifest file")
    parser.add_argument("manifest2", help="Path to second SHA256 manifest file")
    
    args = parser.parse_args()
    
    # Validate input files
    for filepath in [args.manifest1, args.manifest2]:
        if not Path(filepath).exists():
            print(f"Error: File does not exist: {filepath}")
            sys.exit(1)
    
    compare_manifests(args.manifest1, args.manifest2)

if __name__ == "__main__":
    main()