#!/usr/bin/env python3
"""
Download files from World Bank Reproducible Research Repository.

Version: 1.0.2

This script downloads the replication package, reproducibility verification report,
and README from a World Bank Reproducible Research Repository record using the
catalog API. It's designed for replication workflows where researchers need
to download published datasets, code, and verification materials.

Usage:
    python3 tools/download_worldbank.py DOI_OR_ID_OR_URL

Examples:
    # Using full DOI
    python3 tools/download_worldbank.py https://doi.org/10.60572/101y-vn15
    python3 tools/download_worldbank.py 10.60572/101y-vn15

    # Using DOI suffix only
    python3 tools/download_worldbank.py 101y-vn15

    # Using catalog URL
    python3 tools/download_worldbank.py https://reproducibility.worldbank.org/index.php/catalog/400

    # Using catalog ID only
    python3 tools/download_worldbank.py 400

This script will:
1. Parse input (DOI, DOI suffix, catalog URL, or catalog ID)
2. If DOI: Resolve the DOI to find the World Bank catalog ID
   If catalog URL/ID: Use it directly
3. Discover available download files from the catalog page and Downloads tab
4. Download files using server-suggested filenames:
   - README.pdf
   - reproducibility_report_[STUDY_ID].pdf
   - [STUDY_ID].zip (automatically unzipped)
5. Create a directory structure: wb-[IDENTIFIER]/
   (where IDENTIFIER is either the DOI suffix or catalog ID)

Features:
- Supports both DOI and direct catalog URL/ID inputs
- Automatic DOI parsing and resolution
- Dynamic discovery of download files
- Proper file naming conventions
- Automatic zip extraction
- Progress indicators
- Smart file type detection
"""

import argparse
import hashlib
import os
import re
import sys
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

# Version information
__version__ = "1.0.2"

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

def parse_input(input_str):
    """
    Parse input to determine if it's a DOI or catalog URL/ID.
    Returns a tuple (input_type, value) where input_type is 'doi' or 'catalog'.
    """
    # Remove any trailing slashes
    input_str = input_str.rstrip('/')

    # Check for catalog URL
    if 'reproducibility.worldbank.org' in input_str and '/catalog/' in input_str:
        # Extract catalog ID from URL
        match = re.search(r'/catalog/(\d+)', input_str)
        if match:
            return ('catalog', match.group(1))
        raise ValueError(f"Could not extract catalog ID from URL: {input_str}")

    # Check if it's just a numeric catalog ID
    if re.match(r'^\d+$', input_str):
        return ('catalog', input_str)

    # Otherwise, treat as DOI input
    return ('doi', input_str)

def extract_doi_suffix(input_str):
    """Extract DOI suffix from various input formats."""
    # Remove any trailing slashes
    input_str = input_str.rstrip('/')

    # Handle different input formats
    if re.match(r'^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}$', input_str):
        # Direct DOI suffix (e.g., "101y-vn15")
        return input_str
    elif 'doi.org' in input_str:
        # Extract from DOI URL (e.g., "https://doi.org/10.60572/101y-vn15")
        match = re.search(r'/([a-zA-Z0-9]{4}-[a-zA-Z0-9]{4})$', input_str)
        if match:
            return match.group(1)
    elif '10.60572/' in input_str:
        # Extract from DOI format (e.g., "10.60572/101y-vn15")
        match = re.search(r'10\.60572/([a-zA-Z0-9]{4}-[a-zA-Z0-9]{4})', input_str)
        if match:
            return match.group(1)
    else:
        # Fallback: try to extract DOI suffix pattern at the end
        match = re.search(r'([a-zA-Z0-9]{4}-[a-zA-Z0-9]{4})$', input_str)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract DOI suffix from: {input_str}")

def get_catalog_info_direct(catalog_id):
    """Get catalog information directly from catalog ID (without DOI resolution)."""
    catalog_url = f"https://reproducibility.worldbank.org/index.php/catalog/{catalog_id}"

    print(f"🌐 Accessing catalog: {catalog_url}")

    spinner = Spinner("Loading catalog page")
    spinner.start()

    try:
        session = requests.Session()

        # Add headers to mimic a real browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # Get the catalog page
        response = session.get(catalog_url)
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code} when accessing catalog {catalog_id}")

        spinner.stop()

        page_content = response.text

        # Debug: check if page is empty
        if not page_content.strip():
            raise Exception("Empty page content received")

        print(f"✅ Catalog page loaded")

        # Extract download IDs by looking for download links in HTML
        download_pattern = rf'catalog/{catalog_id}/download/(\d+)'
        html_download_ids = set(re.findall(download_pattern, page_content))

        print(f"🔍 Found download IDs in main page: {sorted(html_download_ids, key=int)}")

        # Also check the related-materials page which contains the Downloads tab content
        try:
            related_materials_url = f"https://reproducibility.worldbank.org/index.php/catalog/{catalog_id}/related-materials"
            related_response = session.get(related_materials_url)
            if related_response.status_code == 200:
                related_content = related_response.text
                related_download_ids = set(re.findall(download_pattern, related_content))
                if related_download_ids:
                    print(f"🔍 Found download IDs in related-materials page: {sorted(related_download_ids, key=int)}")
                    html_download_ids.update(related_download_ids)
        except Exception as e:
            print(f"⚠️  Could not fetch related-materials page: {e}")

        # Only use files explicitly linked in the Downloads tab
        # Note: World Bank server doesn't validate catalog/download associations,
        # so probing for additional files can return files from other catalogs
        download_ids = sorted(html_download_ids, key=int)

        if not download_ids:
            print("DEBUG: Looking for 'download' in page content...")
            download_occurrences = [m.start() for m in re.finditer('download', page_content.lower())]
            print(f"Found 'download' at positions: {download_occurrences[:10]}...")
            raise Exception("Could not find any download links")

        print(f"🔍 Total download IDs found: {download_ids}")

        return catalog_id, download_ids

    except Exception as e:
        spinner.stop()
        raise Exception(f"Failed to get catalog info: {e}")

def resolve_catalog_info(doi_suffix):
    """Resolve DOI to get catalog ID and discover download IDs."""
    full_doi = f"https://doi.org/10.60572/{doi_suffix}"

    print(f"🌐 Resolving DOI: {full_doi}")

    spinner = Spinner("Resolving DOI")
    spinner.start()

    try:
        # Follow all redirects manually to see the sequence
        session = requests.Session()
        
        # Add headers to mimic a real browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        current_url = full_doi
        redirect_count = 0
        max_redirects = 10
        
        while redirect_count < max_redirects:
            response = session.get(current_url, allow_redirects=False)
            
            if response.status_code in (301, 302, 303, 307, 308):
                # Follow redirect
                redirect_count += 1
                new_url = response.headers.get('Location')
                if not new_url:
                    break
                
                # Handle relative URLs
                if new_url.startswith('/'):
                    from urllib.parse import urljoin
                    new_url = urljoin(current_url, new_url)
                
                print(f"🔄 Redirect {redirect_count}: {current_url} -> {new_url}")
                current_url = new_url
            elif response.status_code == 200:
                # Final destination reached
                break
            else:
                raise Exception(f"HTTP {response.status_code} at {current_url}")
        
        if redirect_count >= max_redirects:
            raise Exception("Too many redirects")
        
        # Now get the final page content
        final_response = session.get(current_url)
        if final_response.status_code != 200:
            raise Exception(f"HTTP {final_response.status_code} at final URL: {current_url}")
        
        spinner.stop()
        
        final_url = current_url
        print(f"✅ Final URL: {final_url}")
        
        # Handle the newer study URL format - check for HTTP Refresh header
        if '/catalog/study/' in final_url:
            print("🔍 Detected study URL format, checking for HTTP refresh redirect...")
            
            # Check for HTTP Refresh header (this is the key!)
            refresh_header = final_response.headers.get('Refresh', '')
            if refresh_header:
                print(f"✅ Found HTTP Refresh header: {refresh_header}")
                
                # Parse the refresh header to extract the URL
                # Format is typically: "0;url=https://..."
                refresh_match = re.search(r'url=(.+)', refresh_header)
                if refresh_match:
                    catalog_url = refresh_match.group(1)
                    print(f"🔄 Following HTTP refresh to: {catalog_url}")
                    
                    # Follow the refresh redirect
                    final_response = session.get(catalog_url)
                    if final_response.status_code == 200:
                        final_url = catalog_url
                        print(f"✅ Successfully redirected to catalog: {final_url}")
                    else:
                        raise Exception(f"Failed to access catalog URL: {catalog_url} (HTTP {final_response.status_code})")
                else:
                    raise Exception(f"Could not parse refresh header: {refresh_header}")
            else:
                print("⚠️  No HTTP Refresh header found, trying other methods...")
                
                # Fallback: try to get page content and look for meta refresh or other redirects
                page_content = final_response.text
                
                # Look for meta refresh in HTML
                meta_refresh = re.search(r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\'][^"\']*url=([^"\']*)["\'][^>]*>', page_content, re.IGNORECASE)
                if meta_refresh:
                    redirect_url = meta_refresh.group(1)
                    print(f"🔄 Found meta refresh: {redirect_url}")
                    if redirect_url.startswith('/'):
                        from urllib.parse import urljoin
                        redirect_url = urljoin(final_url, redirect_url)
                    
                    final_response = session.get(redirect_url)
                    final_url = redirect_url
                    print(f"✅ Redirected via meta refresh to: {final_url}")
                else:
                    # Extract study ID and try to construct catalog URL
                    study_match = re.search(r'/catalog/study/([^/?]+)', final_url)
                    if study_match:
                        study_id = study_match.group(1)
                        print(f"📋 Study ID: {study_id}")
                        print("⚠️  No automatic redirect found - this may require manual mapping")
                        raise Exception(f"Could not automatically resolve study URL to catalog URL for study ID: {study_id}")
                    else:
                        raise Exception("Could not extract study ID from URL")
        
        # Get the page content to extract download information
        page_content = final_response.text
        
        # Debug: check if page is empty
        if not page_content.strip():
            raise Exception("Empty page content received")
        
        # Try multiple patterns to extract catalog ID
        catalog_id = None
        
        # Pattern 1: Look for download links in the page
        catalog_match = re.search(r'catalog/(\d+)/download', page_content)
        if catalog_match:
            catalog_id = catalog_match.group(1)
        
        # Pattern 2: Extract from URL if it contains catalog ID
        if not catalog_id:
            url_match = re.search(r'catalog/(\d+)', final_url)
            if url_match:
                catalog_id = url_match.group(1)
        
        # Pattern 3: Look for catalog references in the HTML
        if not catalog_id:
            catalog_refs = re.findall(r'catalog[/=](\d+)', page_content)
            if catalog_refs:
                catalog_id = catalog_refs[0]  # Take the first one found
        
        if not catalog_id:
            # Debug: show more information
            print("DEBUG: Final URL:", final_url)
            print("DEBUG: Page content length:", len(page_content))
            print("DEBUG: First 1000 characters of page:")
            print(repr(page_content[:1000]))
            print("DEBUG: Looking for 'catalog' in content...")
            catalog_occurrences = [m.start() for m in re.finditer('catalog', page_content.lower())]
            print(f"Found 'catalog' at positions: {catalog_occurrences[:10]}...")
            raise Exception("Could not extract catalog ID from page content")
        
        print(f"📦 Catalog ID: {catalog_id}")
        
        # Extract download IDs by looking for download links in HTML
        download_pattern = rf'catalog/{catalog_id}/download/(\d+)'
        html_download_ids = set(re.findall(download_pattern, page_content))

        print(f"🔍 Found download IDs in main page: {sorted(html_download_ids, key=int)}")

        # Also check the related-materials page which contains the Downloads tab content
        try:
            related_materials_url = f"https://reproducibility.worldbank.org/index.php/catalog/{catalog_id}/related-materials"
            related_response = session.get(related_materials_url)
            if related_response.status_code == 200:
                related_content = related_response.text
                related_download_ids = set(re.findall(download_pattern, related_content))
                if related_download_ids:
                    print(f"🔍 Found download IDs in related-materials page: {sorted(related_download_ids, key=int)}")
                    html_download_ids.update(related_download_ids)
        except Exception as e:
            print(f"⚠️  Could not fetch related-materials page: {e}")

        # Only use files explicitly linked in the Downloads tab
        # Note: World Bank server doesn't validate catalog/download associations,
        # so probing for additional files can return files from other catalogs
        download_ids = sorted(html_download_ids, key=int)
        
        if not download_ids:
            print("DEBUG: Looking for 'download' in page content...")
            download_occurrences = [m.start() for m in re.finditer('download', page_content.lower())]
            print(f"Found 'download' at positions: {download_occurrences[:10]}...")  # Show first 10
            raise Exception("Could not find any download links")
        
        print(f"🔍 Total download IDs found: {download_ids}")
        
        return catalog_id, download_ids
        
    except Exception as e:
        spinner.stop()
        raise Exception(f"Failed to resolve DOI: {e}")

def identify_file_type(url, headers=None):
    """Identify file type based on headers and heuristics."""
    if not headers:
        try:
            response = requests.head(url)
            headers = response.headers
        except:
            return "unknown", None
    
    content_type = headers.get('content-type', '').lower()
    content_disposition = headers.get('content-disposition', '')
    
    # Extract filename from Content-Disposition if available
    filename = ""
    if content_disposition and 'filename=' in content_disposition:
        filename = content_disposition.split('filename=')[1].strip('"').strip("'").lower()
    
    # Check file type based on filename first (more reliable than content-type)
    if filename.endswith('.pdf'):
        return "pdf", content_disposition
    elif filename.endswith('.zip'):
        return "zip", content_disposition
    elif filename.endswith(('.txt', '.md', '.readme')):
        return "text", content_disposition
    
    # Fallback to content type
    if 'application/pdf' in content_type:
        return "pdf", content_disposition
    elif 'application/zip' in content_type:
        return "zip", content_disposition
    elif 'text/plain' in content_type:
        return "text", content_disposition
    elif 'application/octet-stream' in content_type:
        # octet-stream is generic - try to guess from filename or context
        if 'readme' in filename or 'readme' in content_disposition.lower():
            if filename.endswith('.pdf'):
                return "pdf", content_disposition
            else:
                return "text", content_disposition
        elif filename.endswith('.zip') or 'zip' in content_disposition.lower():
            return "zip", content_disposition
        else:
            return "unknown", content_disposition
    
    return "unknown", content_disposition

def download_file(url, filepath, description="file"):
    """Download a file from URL."""
    print(f"⬇️  Downloading: {description}")
    
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            
            # Get total file size if available
            total_size = int(response.headers.get('content-length', 0))
            
            spinner = Spinner(f"Downloading {description}", total_size)
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
            print(f"✅ {final_info}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        if 'spinner' in locals():
            spinner.stop()
        print(f"❌ Error downloading {description}: {e}")
        return False

def unzip_file(zip_path, extract_to):
    """Extract a zip file."""
    print(f"📦 Unzipping: {zip_path.name}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✅ Unzipped to: {extract_to}")
        return True
    except Exception as e:
        print(f"❌ Failed to unzip {zip_path.name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Download files from World Bank Reproducible Research Repository')
    parser.add_argument('doi_or_id', help='World Bank repository identifier (DOI suffix, DOI, DOI URL, catalog URL, or catalog ID)')
    parser.add_argument('--output', default='.', help='Output directory (default: current directory)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be downloaded without actually downloading')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    args = parser.parse_args()

    # Print version as first line of output
    print(f"World Bank Download Script - Version {__version__}")

    # Parse input to determine type
    try:
        input_type, value = parse_input(args.doi_or_id)
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Expected formats:")
        print("  - DOI suffix: 101y-vn15")
        print("  - DOI URL: https://doi.org/10.60572/101y-vn15")
        print("  - DOI: 10.60572/101y-vn15")
        print("  - Catalog URL: https://reproducibility.worldbank.org/index.php/catalog/400")
        print("  - Catalog ID: 400")
        sys.exit(1)

    # Process based on input type
    if input_type == 'catalog':
        catalog_id = value
        print(f"🏷️  Catalog ID: {catalog_id}")
        identifier = catalog_id
    else:  # DOI
        try:
            doi_suffix = extract_doi_suffix(value)
            print(f"🏷️  DOI suffix: {doi_suffix}")
            identifier = doi_suffix
        except ValueError as e:
            print(f"❌ Error: {e}")
            print("Expected formats:")
            print("  - DOI suffix: 101y-vn15")
            print("  - DOI URL: https://doi.org/10.60572/101y-vn15")
            print("  - DOI: 10.60572/101y-vn15")
            sys.exit(1)

    # Create output directory
    output_dir = Path(args.output) / f"wb-{identifier}"
    if not args.dry_run:
        if output_dir.exists():
            print(f"❌ Error: {output_dir} already exists - please remove prior to downloading")
            sys.exit(1)
        output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📂 Output directory: {output_dir}")

    try:
        # Get catalog ID and discover download IDs
        if input_type == 'catalog':
            catalog_id, download_ids = get_catalog_info_direct(catalog_id)
        else:  # DOI
            catalog_id, download_ids = resolve_catalog_info(doi_suffix)
    except Exception as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Base URL for downloads
    base_url = f"https://reproducibility.worldbank.org/index.php/catalog/{catalog_id}/download"
    
    # Current date for verification report filename
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n📦 Found {len(download_ids)} file(s) to download:")
    
    if args.dry_run:
        for i, download_id in enumerate(download_ids, 1):
            file_url = f"{base_url}/{download_id}"
            try:
                response = requests.head(file_url)
                file_type, content_disposition = identify_file_type(file_url, response.headers)
                content_length = response.headers.get('content-length', 'Unknown')
                print(f"  {i}. Download ID {download_id}: {file_type} ({content_length} bytes)")
                if content_disposition:
                    print(f"     Content-Disposition: {content_disposition}")
            except Exception as e:
                print(f"  {i}. Download ID {download_id}: Error checking file - {e}")
        
        print(f"\n🔍 Dry run completed. No files were downloaded.")
        return
    
    # Download and process each file
    downloaded_files = []
    failed_downloads = []
    pdf_count = 0  # Track PDF files to determine naming

    for i, download_id in enumerate(download_ids, 1):
        file_url = f"{base_url}/{download_id}"

        print(f"\n📋 Processing file {i}/{len(download_ids)} (Download ID: {download_id})")

        try:
            # Identify file type
            file_type, content_disposition = identify_file_type(file_url)

            # Determine filename - use server-suggested name from Content-Disposition
            if content_disposition and 'filename=' in content_disposition:
                # Extract filename from Content-Disposition header
                filename = content_disposition.split('filename=')[1].strip('"').strip("'")
            elif file_type == "pdf":
                # Fallback naming if no Content-Disposition
                pdf_count += 1
                if pdf_count == 1:
                    filename = "README.pdf"
                else:
                    filename = f"reproducibility-wb-{identifier}.{current_date}.pdf"
            elif file_type == "zip":
                # Fallback naming if no Content-Disposition
                filename = f"wb-{identifier}.zip"
            else:
                # Default naming for unknown types
                filename = f"download-{download_id}"
            
            file_path = output_dir / filename
            
            print(f"🎯 File type: {file_type}, saving as: {filename}")
            
            # Download the file
            if download_file(file_url, file_path, filename):
                downloaded_files.append(filename)
                
                # If this is a zip file, unzip it
                if file_type == "zip":
                    if unzip_file(file_path, output_dir):
                        print(f"💡 You may want to remove the zip file: {filename}")
            else:
                failed_downloads.append(download_id)
                
        except Exception as e:
            print(f"❌ Error processing download ID {download_id}: {e}")
            failed_downloads.append(download_id)
    
    # Summary
    print(f"\n🎉 Download process completed!")
    print(f"✅ Successfully downloaded: {len(downloaded_files)} files")
    
    if downloaded_files:
        print("📁 Downloaded files:")
        for filename in downloaded_files:
            print(f"  - {filename}")
    
    if failed_downloads:
        print(f"❌ Failed downloads: {len(failed_downloads)} files")
        print(f"   Download IDs: {failed_downloads}")
        sys.exit(1)
    
    print(f"\n📂 All files saved to: {output_dir}")
    print(f"\n📋 Contents of {output_dir}:")
    try:
        for item in sorted(output_dir.iterdir()):
            if item.is_file():
                size = item.stat().st_size
                print(f"  📄 {item.name} ({size:,} bytes)")
            elif item.is_dir():
                print(f"  📁 {item.name}/")
    except Exception:
        print("  (Could not list directory contents)")

if __name__ == '__main__':
    main()