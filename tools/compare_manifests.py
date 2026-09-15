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

def create_summary(manifest1_path, manifest2_path):
    """Create summary statistics for manifest comparison."""
    # Parse both manifests
    files1, checksums1, basenames1 = parse_manifest(manifest1_path)
    files2, checksums2, basenames2 = parse_manifest(manifest2_path)
    
    # Calculate differences
    files_only_in_1 = set(files1.keys()) - set(files2.keys())
    files_only_in_2 = set(files2.keys()) - set(files1.keys())
    common_basenames = set(basenames1.keys()) & set(basenames2.keys())
    common_checksums = set(checksums1.keys()) & set(checksums2.keys())
    
    # Find exact matches and mismatches
    exact_matches = []
    basename_checksum_mismatches = []
    
    for basename in common_basenames:
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
    
    return {
        'files1': files1,
        'files2': files2,
        'checksums1': checksums1,
        'checksums2': checksums2,
        'basenames1': basenames1,
        'basenames2': basenames2,
        'files_only_in_1': files_only_in_1,
        'files_only_in_2': files_only_in_2,
        'common_basenames': common_basenames,
        'common_checksums': common_checksums,
        'exact_matches': exact_matches,
        'basename_checksum_mismatches': basename_checksum_mismatches
    }

def compare_manifests(manifest1_path, manifest2_path):
    """Compare two manifest files and report overlaps."""
    
    # Get summary data
    summary = create_summary(manifest1_path, manifest2_path)
    
    # Print summary first
    print("📊 SUMMARY:")
    print()
    print(f"- Total files in manifest 1: {len(summary['files1'])}")
    print(f"- Total files in manifest 2: {len(summary['files2'])}")
    print(f"- Files only in manifest 1: {len(summary['files_only_in_1'])}")
    print(f"- Files only in manifest 2: {len(summary['files_only_in_2'])}")
    print(f"- Common basenames: {len(summary['common_basenames'])}")
    print(f"- Common checksums: {len(summary['common_checksums'])}")
    print(f"- Exact matches: {len(summary['exact_matches'])}")
    print(f"- Same basename, different checksum: {len(summary['basename_checksum_mismatches'])}")
    print()
    
    print(f"Comparing manifests:")
    print()
    print(f"- File 1 ({manifest1_path}) contains {len(summary['files1'])} entries")
    print(f"- File 2 ({manifest2_path}) contains {len(summary['files2'])} entries")
    print()
    
    # Report files that appear only in each manifest
    print("📄 FILES THAT APPEAR ONLY IN MANIFEST 1:")
    print()
    print(f"Found {len(summary['files_only_in_1'])} files only in manifest 1")
    if summary['files_only_in_1']:
        for filename in sorted(summary['files_only_in_1']):
            print(f"  {filename}")
        print()
    
    print("📄 FILES THAT APPEAR ONLY IN MANIFEST 2:")
    print()
    print(f"Found {len(summary['files_only_in_2'])} files only in manifest 2")
    if summary['files_only_in_2']:
        for filename in sorted(summary['files_only_in_2']):
            print(f"  {filename}")
        print()
    
    # Report results
    print("📁 BASENAMES THAT APPEAR IN BOTH MANIFESTS:")
    print()
    print(f"Found {len(summary['common_basenames'])} common basenames")
    if summary['common_basenames']:
        for basename in sorted(summary['common_basenames']):
            files_in_1 = summary['basenames1'][basename]
            files_in_2 = summary['basenames2'][basename]
            print(f"  {basename}")
            print(f"    In manifest 1: {', '.join(files_in_1)}")
            print(f"    In manifest 2: {', '.join(files_in_2)}")
        print()
    
    print("🔍 CHECKSUMS THAT APPEAR IN BOTH MANIFESTS:")
    print()
    print(f"Found {len(summary['common_checksums'])} common checksums")
    if summary['common_checksums']:
        for checksum in sorted(summary['common_checksums']):
            files_in_1 = summary['checksums1'][checksum]
            files_in_2 = summary['checksums2'][checksum]
            print(f"- {checksum}")
            print(f"  - In manifest 1: {', '.join(files_in_1)}")
            print(f"  - In manifest 2: {', '.join(files_in_2)}")
            print()
    
    print("✅ EXACT MATCHES (same basename and checksum):")
    print()
    print(f"Found {len(summary['exact_matches'])} exact matches")
    if summary['exact_matches']:
        for basename, file1, file2, checksum in sorted(summary['exact_matches']):
            print(f"- {checksum}")
            print(f"  - In manifest 1: {file1}")
            print(f"  - In manifest 2: {file2}")
            print()
    
    print("⚠️  BASENAME MATCHES WITH DIFFERENT CHECKSUMS:")
    print()
    print("*This compares all files with the same name, regardless of path.*")
    print()
    print(f"Found {len(summary['basename_checksum_mismatches'])} files with same basename but different checksums")
    if summary['basename_checksum_mismatches']:
        for basename, file1, checksum1, file2, checksum2 in sorted(summary['basename_checksum_mismatches']):
            print(f"- {basename}")
            print(f"  - Manifest 1: {file1} -> {checksum1}")
            print(f"  - Manifest 2: {file2} -> {checksum2}")
            print()
    

def create_summary_file(manifest1_path, manifest2_path, summary_file_path):
    """Create a separate summary file with just the key statistics."""
    summary = create_summary(manifest1_path, manifest2_path)
    
    # Write summary to file
    with open(summary_file_path, 'w') as f:
        f.write("# Manifest Comparison Summary\n\n")
        f.write(f"**Generated:** {Path(manifest1_path).name} vs {Path(manifest2_path).name}\n\n")
        f.write("## Key Statistics\n\n")
        f.write(f"- Total files in manifest 1: {len(summary['files1'])}\n")
        f.write(f"- Total files in manifest 2: {len(summary['files2'])}\n")
        f.write(f"- Files only in manifest 1: {len(summary['files_only_in_1'])}\n")
        f.write(f"- Files only in manifest 2: {len(summary['files_only_in_2'])}\n")
        f.write(f"- Common basenames: {len(summary['common_basenames'])}\n")
        f.write(f"- Common checksums: {len(summary['common_checksums'])}\n")
        f.write(f"- Exact matches: {len(summary['exact_matches'])}\n")
        f.write(f"- Same basename, different checksum: {len(summary['basename_checksum_mismatches'])}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Compare two SHA256 manifest files and identify overlaps",
        epilog="Example: python compare_manifests.py manifest-1-sha256sum manifest-2-sha256sum"
    )
    parser.add_argument("manifest1", help="Path to first SHA256 manifest file")
    parser.add_argument("manifest2", help="Path to second SHA256 manifest file")
    parser.add_argument("--summary-file", help="Path to create a separate summary file")
    
    args = parser.parse_args()
    
    # Validate input files
    for filepath in [args.manifest1, args.manifest2]:
        if not Path(filepath).exists():
            print(f"Error: File does not exist: {filepath}")
            sys.exit(1)
    
    compare_manifests(args.manifest1, args.manifest2)
    
    # Create summary file if requested
    if args.summary_file:
        create_summary_file(args.manifest1, args.manifest2, args.summary_file)

if __name__ == "__main__":
    main()