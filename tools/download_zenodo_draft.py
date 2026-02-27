#!/usr/bin/env python3
"""
Download files from a Zenodo draft deposit using the Zenodo API.
This script can handle draft deposits that require authentication.

Usage:
    python3 tools/download_zenodo_draft.py RECORD_ID [--access-token TOKEN]

Examples:
    # Download all files
    python3 tools/download_zenodo_draft.py 123456 --access-token your_token_here
    
    # Show what would be downloaded (dry run)
    python3 tools/download_zenodo_draft.py 123456 --sandbox --dry-run
    
    # Download only specific files (use numbers from dry-run output)
    python3 tools/download_zenodo_draft.py 123456 --files "1,3,5"
    python3 tools/download_zenodo_draft.py 123456 --files "2"

Environment Variables:
    ZENODO_ACCESS_TOKEN or ZENODO_TOKEN - Zenodo access token
    
.env file support:
    Create a .env file with: ZENODO_ACCESS_TOKEN=your_token_here
    (requires python-dotenv: pip install python-dotenv)

This script will:
1. Connect to Zenodo API (production or sandbox)
2. Fetch metadata for the specified draft deposit
3. Skip files that already exist with matching checksums
4. Download selected files (or all files) to a directory named 'zenodo-RECORD_ID'
5. Preserve checksums from Zenodo metadata in generated/manifest.zenodo-RECORD_ID.DATE.{sha256,md5}
6. Create metadata file with file sizes in generated/metadata.zenodo-RECORD_ID.txt

Features:
- Smart resuming: Won't re-download files that already exist with correct checksums
- Selective download: Choose specific files by number (use --dry-run first to see file numbers)
- Multiple authentication methods: command line, environment variables, or .env file

Note: You need a Zenodo access token to access draft deposits. Get one from:
- Production: https://zenodo.org/account/settings/applications/tokens/new/
- Sandbox: https://sandbox.zenodo.org/account/settings/applications/tokens/new/

Token priority order:
1. Command line --access-token argument
2. ZENODO_ACCESS_TOKEN or ZENODO_TOKEN environment variable
3. .env file with ZENODO_ACCESS_TOKEN or ZENODO_TOKEN
"""

import argparse
import hashlib
import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

# Try to load python-dotenv for .env file support
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

ZENODO_API_BASE = "https://zenodo.org/api"
SANDBOX_API_BASE = "https://sandbox.zenodo.org/api"

class Spinner:
    """Progress spinner with download information."""
    def __init__(self, message="Loading", total_size=0):
        self.spinner_chars = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']  # Braille block spinner animation frames
        self.message = message
        self.total_size = total_size
        self.downloaded_size = 0
        self.running = False
        self.thread = None
        self.idx = 0
    
    def update_progress(self, downloaded_size):
        """Update the download progress."""
        self.downloaded_size = downloaded_size
    
    def format_bytes(self, bytes_val):
        """Format bytes into human readable format."""
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024**2:
            return f"{bytes_val/1024:.1f} KB"
        elif bytes_val < 1024**3:
            return f"{bytes_val/(1024**2):.1f} MB"
        else:
            return f"{bytes_val/(1024**3):.1f} GB"
    
    def spin(self):
        while self.running:
            char = self.spinner_chars[self.idx % len(self.spinner_chars)]
            progress_info = f"Downloaded: {self.format_bytes(self.downloaded_size)}"
            
            if self.total_size > 0:
                percentage = (self.downloaded_size / self.total_size) * 100
                progress_info += f" of {self.format_bytes(self.total_size)} ({percentage:.1f}%)"
            
            print(f"\r{char} {progress_info}", end="", flush=True)
            self.idx += 1
            time.sleep(0.1)
    
    def start(self):
        # Don't start spinner in CI environments
        is_ci = os.getenv("CI")
        if not is_ci:
            self.running = True
            self.thread = threading.Thread(target=self.spin)
            self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        print("\r" + " " * (len(self.message) + 10), end="")  # Clear the line
        print("\r", end="", flush=True)

def calculate_checksum(filepath, algorithm='md5'):
    """Calculate checksum for a file."""
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def file_exists_with_checksum(filepath, expected_checksum):
    """Check if a file exists and has the expected checksum."""
    if not os.path.exists(filepath):
        return False
    
    if not expected_checksum:
        # If no checksum provided, just check if file exists
        return True
    
    # Parse checksum format (algorithm:hash or just hash)
    if ':' in expected_checksum:
        algorithm, expected_hash = expected_checksum.split(':', 1)
        algorithm = algorithm.lower()
        if algorithm in ['sha-256', 'sha256']:
            algorithm = 'sha256'
    else:
        # Assume MD5 if no algorithm specified
        algorithm = 'md5'
        expected_hash = expected_checksum
    
    try:
        actual_hash = calculate_checksum(filepath, algorithm)
        return actual_hash.lower() == expected_hash.lower()
    except Exception:
        return False

def get_record_metadata(record_id, access_token, sandbox=False):
    """Get record metadata from Zenodo API."""
    base_url = SANDBOX_API_BASE if sandbox else ZENODO_API_BASE
    url = f"{base_url}/deposit/depositions/{record_id}"
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    print(f"🌐 Fetching metadata from: {url}")
    
    spinner = Spinner("Connecting to Zenodo API")
    spinner.start()
    
    try:
        response = requests.get(url, headers=headers)
        spinner.stop()
        
        if response.status_code == 401:
            print("❌ Error: Unauthorized. Please check your access token.")
            sys.exit(1)
        elif response.status_code == 404:
            print(f"❌ Error: Record {record_id} not found.")
            sys.exit(1)
        elif response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code} - {response.text}")
            sys.exit(1)
        
        print("✅ Successfully retrieved metadata!")
        return response.json()
    except Exception as e:
        spinner.stop()
        print(f"❌ Error: {e}")
        raise

def download_file(url, filepath, access_token):
    """Download a file from URL with authentication."""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    print(f"⬇️  Downloading: {filepath.name}")
    
    try:
        with requests.get(url, headers=headers, stream=True) as response:
            response.raise_for_status()
            
            # Get total file size if available
            total_size = int(response.headers.get('content-length', 0))
            
            spinner = Spinner(f"Downloading {filepath.name}", total_size)
            spinner.start()
            
            # Create parent directories if they don't exist
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            downloaded_size = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    spinner.update_progress(downloaded_size)
        
        spinner.stop()
        
        # Show final download info
        is_ci = os.getenv("CI")
        final_info = f"Downloaded: {spinner.format_bytes(downloaded_size)}"
        if total_size > 0:
            final_info += f" of {spinner.format_bytes(total_size)} (100.0%)"
        
        if is_ci:
            print(f"{final_info}")
        else:
            print(f"\n✅ {final_info}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        if 'spinner' in locals():
            spinner.stop()
        print(f"❌ Error downloading {filepath.name}: {e}")
        return False

def save_checksums(output_dir, files_metadata):
    """Save checksums to files following the current naming conventions."""
    if not files_metadata:
        return
    
    # Create generated directory if it doesn't exist
    generated_dir = Path("generated")
    generated_dir.mkdir(exist_ok=True)
    
    # Get the directory name for tag
    dir_name = Path(output_dir).name
    
    # Create checksum files with current naming convention
    date_str = datetime.now().strftime("%Y-%m-%d")
    sha256_file = generated_dir / f"manifest.{dir_name}.{date_str}.sha256"
    md5_file = generated_dir / f"manifest.{dir_name}.{date_str}.md5"
    metadata_file = generated_dir / f"metadata.{dir_name}.txt"
    
    print(f"Saving checksums to {sha256_file} and {md5_file}")
    
    # Write metadata file (filename,bytes)
    with open(metadata_file, 'w') as f:
        f.write("filename,bytes\n")
        for file_info in files_metadata:
            rel_path = os.path.relpath(file_info['local_path'], output_dir)
            f.write(f"./{rel_path},{file_info['size']}\n")
    
    # Write SHA256 checksums if available
    sha256_checksums = []
    md5_checksums = []
    
    for file_info in files_metadata:
        rel_path = os.path.relpath(file_info['local_path'], output_dir)
        
        # Use Zenodo-provided checksums if available
        if 'checksum' in file_info and file_info['checksum']:
            checksum_str = file_info['checksum']
            # Zenodo typically provides checksums in format "algorithm:hash"
            if ':' in checksum_str:
                algorithm, hash_value = checksum_str.split(':', 1)
                if algorithm.lower() == 'md5':
                    md5_checksums.append(f"{hash_value}  ./{rel_path}")
                elif algorithm.lower() in ['sha256', 'sha-256']:
                    sha256_checksums.append(f"{hash_value}  ./{rel_path}")
            else:
                # Assume it's MD5 if no algorithm specified (common default)
                md5_checksums.append(f"{checksum_str}  ./{rel_path}")
        
        # Calculate local checksums if file exists and no remote checksum
        if os.path.exists(file_info['local_path']):
            if not any(f"./{rel_path}" in line for line in sha256_checksums):
                sha256_hash = calculate_checksum(file_info['local_path'], 'sha256')
                sha256_checksums.append(f"{sha256_hash}  ./{rel_path}")
            
            if not any(f"./{rel_path}" in line for line in md5_checksums):
                md5_hash = calculate_checksum(file_info['local_path'], 'md5')
                md5_checksums.append(f"{md5_hash}  ./{rel_path}")
    
    # Write checksum files
    if sha256_checksums:
        with open(sha256_file, 'w') as f:
            for line in sorted(sha256_checksums):
                f.write(line + '\n')
    
    if md5_checksums:
        with open(md5_file, 'w') as f:
            for line in sorted(md5_checksums):
                f.write(line + '\n')

def get_access_token(provided_token=None):
    """Get access token from various sources in order of preference."""
    # 1. Command line argument (highest priority)
    if provided_token:
        return provided_token
    
    # 2. Environment variables
    token = os.getenv('ZENODO_ACCESS_TOKEN') or os.getenv('ZENODO_TOKEN')
    if token:
        return token
    
    # 3. Check for .env file (if dotenv is available)
    if DOTENV_AVAILABLE and os.path.exists('.env'):
        # Re-load in case .env was created after script started
        load_dotenv(override=True)
        token = os.getenv('ZENODO_ACCESS_TOKEN') or os.getenv('ZENODO_TOKEN')
        if token:
            return token
    
    return None

def main():
    parser = argparse.ArgumentParser(description='Download files from a Zenodo draft deposit')
    parser.add_argument('record_id', help='Zenodo record/deposit ID')
    parser.add_argument('--access-token', help='Zenodo access token (can also be set via ZENODO_ACCESS_TOKEN or ZENODO_TOKEN environment variable, or in .env file)')
    parser.add_argument('--output', default='.', help='Output directory (default: current directory)')
    parser.add_argument('--sandbox', action='store_true', help='Use Zenodo sandbox instead of production')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be downloaded without actually downloading')
    parser.add_argument('--files', type=str, help='Comma-separated list of file numbers to download (e.g., "1,3,5" or "2"). Use --dry-run first to see file numbers.')
    
    args = parser.parse_args()
    
    # Get access token from various sources
    access_token = get_access_token(args.access_token)
    
    if not access_token:
        print("❌ Error: No access token provided.")
        print("Please provide an access token via:")
        print("  1. 💻 Command line: --access-token YOUR_TOKEN")
        print("  2. 🌍 Environment variable: ZENODO_ACCESS_TOKEN or ZENODO_TOKEN")
        if DOTENV_AVAILABLE:
            print("  3. 📄 .env file with ZENODO_ACCESS_TOKEN=your_token")
        else:
            print("  3. 📦 Install python-dotenv to use .env file support")
        sys.exit(1)
    
    # Clean record ID (remove URL parts if full URL provided)
    record_id = args.record_id
    if 'zenodo.org' in record_id:
        # Extract ID from URL like https://zenodo.org/deposit/123456 or https://zenodo.org/record/123456
        parts = record_id.split('/')
        record_id = parts[-1]
    
    print(f"🏷️  Zenodo Record ID: {record_id}")
    print(f"🔧 Using {'sandbox' if args.sandbox else 'production'} API")
    
    # Create output directory
    output_dir = Path(args.output) / f"zenodo-{record_id}"
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Output directory: {output_dir}")
    
    # Get record metadata
    try:
        metadata = get_record_metadata(record_id, access_token, args.sandbox)
    except Exception as e:
        print(f"❌ Failed to get record metadata: {e}")
        sys.exit(1)
    
    # Extract file information
    files_info = metadata.get('files', [])
    if not files_info:
        print("⚠️  No files found in this deposit.")
        return
    
    print(f"\n📦 Found {len(files_info)} file(s):")
    
    files_metadata = []
    
    # Parse file selection if provided
    selected_files = None
    if args.files:
        try:
            selected_files = set(int(x.strip()) for x in args.files.split(','))
        except ValueError:
            print("❌ Error: Invalid file selection format. Use comma-separated numbers (e.g., '1,3,5').")
            sys.exit(1)
    
    for i, file_info in enumerate(files_info, 1):
        filename = file_info['filename']
        download_url = file_info['links']['download']
        file_size = file_info['filesize']
        checksum = file_info.get('checksum', '')
        
        # Check if this file is selected (if file selection is used)
        if selected_files is not None and i not in selected_files:
            print(f"  {i}. {filename} ({file_size} bytes) [SKIPPED - not selected]")
            continue
        
        local_path = output_dir / filename
        
        # Check if file already exists with correct checksum
        file_exists = file_exists_with_checksum(local_path, checksum)
        status = ""
        if file_exists:
            status = " [EXISTS - will skip download]"
        
        print(f"  {i}. {filename} ({file_size} bytes){status}")
        if checksum:
            print(f"     Checksum: {checksum}")
        
        files_metadata.append({
            'filename': filename,
            'local_path': str(local_path),
            'size': file_size,
            'checksum': checksum,
            'download_url': download_url,
            'file_exists': file_exists,
            'file_number': i
        })
    
    if args.dry_run:
        print(f"\n🔍 Dry run completed. No files were downloaded.")
        if not args.files:
            print(f"💡 To download specific files, use: --files \"1,3\" (comma-separated file numbers)")
        if selected_files:
            print(f"📝 Selected files: {sorted(selected_files)}")
        return
    
    # Download files
    print(f"\n⬇️  Downloading files to {output_dir}...")
    
    failed_downloads = []
    skipped_files = []
    
    for file_meta in files_metadata:
        if file_meta['file_exists']:
            print(f"⏭️  Skipping {file_meta['filename']} (already exists with correct checksum)")
            skipped_files.append(file_meta['filename'])
            continue
            
        success = download_file(
            file_meta['download_url'], 
            Path(file_meta['local_path']), 
            access_token
        )
        if not success:
            failed_downloads.append(file_meta['filename'])
    
    # Save checksums
    if files_metadata:
        save_checksums(str(output_dir), files_metadata)
    
    # Summary
    total_files = len(files_metadata)
    downloaded_files = total_files - len(failed_downloads) - len(skipped_files)
    
    print(f"\n🎉 Process completed!")
    print(f"✅ Successfully downloaded: {downloaded_files} files")
    
    if skipped_files:
        print(f"⏭️  Skipped (already exist): {len(skipped_files)} files")
        for i, filename in enumerate(skipped_files, 1):
            print(f"  {i}. {filename}")
    
    if failed_downloads:
        print(f"❌ Failed downloads: {len(failed_downloads)} files")
        for i, filename in enumerate(failed_downloads, 1):
            print(f"  {i}. {filename}")
        sys.exit(1)
    
    # Git integration (similar to other scripts)
    if os.getenv("CI"):
        print("🤖 CI environment detected, adding files to git...")
        os.system(f"git add -v {output_dir}")
        os.system(f"git commit -m '[skip ci] Adding files from Zenodo draft deposit {record_id}' {output_dir}")
    else:
        print(f"💡 You may want to 'git add' the contents of {output_dir}")

if __name__ == '__main__':
    main()
