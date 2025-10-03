#!/usr/bin/python3
"""
Download files from public openICPSR deposits.

This script downloads all files from a published openICPSR deposit
as a ZIP archive. It's designed for downloading publicly accessible deposits.

Usage:
    python3 tools/openicpsr.py PROJECT_ID

Example:
    python3 tools/openicpsr.py 146462

Arguments:
    PROJECT_ID  - Numeric openICPSR project ID (required)

Features:
    - Downloads from public openICPSR deposits
    - Progress indicator with download size tracking
    - Validates project ID format (must be numeric)

Output:
    - Downloads ZIP file to current directory
    - Prints download location when complete

Requirements:
    - requests: HTTP client library

Note: This tool is for downloading published/public deposits. For private deposits,
use download_openicpsr-private.py instead.
"""

import getpass
import os
import re
import requests
import sys
import time
import yaml

# Authentication handling
mypassword = os.environ.get("ICPSR_PASS")
mylogin = os.environ.get("ICPSR_EMAIL")

try:
    pid = sys.argv[1]
    # Add optional login parameter support
    if len(sys.argv) >= 3:
        mylogin = sys.argv[2]
        print(f"Project ID: {pid}")
        print(f"Login     : {mylogin}")
        mypassword = getpass.getpass()
except IndexError:
    print(f"Usage: {sys.argv[0]} <PROJECT ID> [login]")
    print(f"Or set ICPSR_EMAIL and ICPSR_PASS environment variables")
    exit()

# Validate project ID format (must be numeric)
if not pid.isdigit():
    print(f"Error: Project ID must be numeric. Got '{pid}'")
    print(f"Example: 146462")
    print(f"Usage: {sys.argv[0]} <PROJECT ID> [login]")
    exit(1)

# Check authentication
if mypassword is None or len(mypassword) == 0:
    print(f"Password must be provided via ICPSR_PASS environment variable")
    print(f"or by specifying a login as second argument")
    print(f"Usage: {sys.argv[0]} <PROJECT ID> [login]")
    exit(1)

if mylogin is None or len(mylogin) == 0:
    print(f"Login must be provided via ICPSR_EMAIL environment variable")
    print(f"or by specifying a login as second argument")
    print(f"Usage: {sys.argv[0]} <PROJECT ID> [login]")
    exit(1)

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "DNT": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
}

def format_bytes(bytes_val):
    """Format bytes into human readable format."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024**2:
        return f"{bytes_val/1024:.1f} KB"
    elif bytes_val < 1024**3:
        return f"{bytes_val/(1024**2):.1f} MB"
    else:
        return f"{bytes_val/(1024**3):.1f} GB"

OPENICPSR_URL = "https://www.openicpsr.org/openicpsr/"

with requests.Session() as session:
    # Authenticate with openICPSR using OAuth flow (same as private script)
    print(f"Downloading from openICPSR project {pid}...")

    # Get required session cookies
    print("Getting session cookies...")
    req = session.get(
        OPENICPSR_URL,
        headers=headers,
    )
    req.raise_for_status()

    print("Initiating OAuth flow...")
    headers["Referer"] = OPENICPSR_URL
    login_req = session.get(
        f"{OPENICPSR_URL}login",
        headers=headers,
        allow_redirects=True,
    )
    login_req.raise_for_status()

    # Check if we were redirected to the ICPSR login page
    if 'login.icpsr.umich.edu' in login_req.url:
        print(f"Redirected to ICPSR login at: {login_req.url}")

        # Parse the ICPSR login form
        action_url_pattern = r'<form[^>]*action="([^"]*)"[^>]*method="post"'
        matches = re.findall(action_url_pattern, login_req.text, re.IGNORECASE)
        action_url = matches[0] if matches else login_req.url

        # If the action URL is relative, make it absolute
        if action_url.startswith('/'):
            from urllib.parse import urljoin
            action_url = urljoin(login_req.url, action_url)

        print(f"Submitting login to: {action_url}")
    else:
        # Fallback to original method
        action_url_pattern = r'action="([^"]*)"'
        matches = re.findall(action_url_pattern, login_req.text)
        action_url = matches[0] if matches else None

    data = {
        "username": mylogin,
        "password": mypassword,
    }
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    headers["Referer"] = login_req.url

    print("Logging in...")
    req = session.post(
        action_url,
        headers=headers,
        data=data,
        allow_redirects=True,
    )
    req.raise_for_status()
    headers.pop("Content-Type")

    # Verify we're logged in by checking the final URL or response content
    if 'openicpsr' in req.url:
        print(f"Login successful, redirected to: {req.url}")
    else:
        print(f"Login may have failed, final URL: {req.url}")
        # Continue anyway, might still work

    # Try the same download approach as the private script first
    print("Accessing files...")
    data_url = f"https://deposit.icpsr.umich.edu/deposit/downloadZip?dirPath=/openicpsr/{pid}"

    print("Getting file info...")
    resp = session.get(data_url, headers=headers, allow_redirects=True, stream=True)

    if resp.status_code != 200:
        print(f"Private download method failed (status {resp.status_code}). Trying public project approach...")

        # For public projects, we need to access the project page first
        print("Accessing project page...")
        project_url = f"https://www.openicpsr.org/openicpsr/project/{pid}/version/V1/view"
        project_resp = session.get(project_url, headers=headers, allow_redirects=True)

        if project_resp.status_code != 200:
            print(f"Failed to access project page. Status code: {project_resp.status_code}")
            # Try without version/V1/view
            project_url = f"https://www.openicpsr.org/openicpsr/project/{pid}"
            project_resp = session.get(project_url, headers=headers, allow_redirects=True)
            if project_resp.status_code != 200:
                print(f"Failed to access basic project page. Status code: {project_resp.status_code}")
                exit(1)

        print("Searching for download links in project page...")
        # Look for download links in the HTML
        download_link_patterns = [
            rf'/openicpsr/project/{pid}/version/[^/]+/download[^"]*',
            rf'/openicpsr/project/{pid}/download[^"]*',
            rf'href="([^"]*download[^"]*{pid}[^"]*)"',
            rf'href="([^"]*{pid}[^"]*download[^"]*)"'
        ]

        found_download_url = None
        for pattern in download_link_patterns:
            matches = re.findall(pattern, project_resp.text)
            if matches:
                found_download_url = matches[0]
                if found_download_url.startswith('/'):
                    found_download_url = f"https://www.openicpsr.org{found_download_url}"
                print(f"Found download URL: {found_download_url}")
                break

        # Try the found URL or fall back to standard URLs
        download_urls_to_try = []
        if found_download_url:
            download_urls_to_try.append(found_download_url)

        download_urls_to_try.extend([
            f"https://www.openicpsr.org/openicpsr/project/{pid}/version/V1/download",
            f"https://www.openicpsr.org/openicpsr/project/{pid}/download",
            f"https://www.openicpsr.org/openicpsr/project/{pid}/version/V1/download/terms"
        ])

        resp = None
        for download_url in download_urls_to_try:
            print(f"Trying: {download_url}")
            headers["Referer"] = project_url
            try:
                resp = session.get(download_url, headers=headers, allow_redirects=True, stream=True)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    content_type = resp.headers.get('content-type', '').lower()
                    print(f"Content-Type: {content_type}")

                    # Check if it's a file download
                    if ('application/zip' in content_type or
                        'application/octet-stream' in content_type or
                        'attachment' in resp.headers.get('content-disposition', '')):
                        print("Found file download!")
                        break
                    elif content_type.startswith('text/html'):
                        # Check if this is a terms page that needs acceptance
                        response_text = resp.text.lower()
                        if any(keyword in response_text for keyword in ['accept', 'terms', 'conditions', 'agreement', 'license']):
                            print("Found terms page, extracting actual download URL...")

                            # Look for JavaScript download URL in window.open calls
                            js_download_patterns = [
                                r"window\.open\(['\"]([^'\"]*)['\"]",
                                r"location\.href\s*=\s*['\"]([^'\"]*download[^'\"]*)['\"]",
                                r"href=['\"]([^'\"]*download[^'\"]*)['\"]"
                            ]

                            actual_download_url = None
                            for pattern in js_download_patterns:
                                matches = re.findall(pattern, resp.text)
                                for match in matches:
                                    if 'download' in match and pid in match:
                                        actual_download_url = match
                                        break
                                if actual_download_url:
                                    break

                            if actual_download_url:
                                if actual_download_url.startswith('/'):
                                    actual_download_url = f"https://www.openicpsr.org{actual_download_url}"
                                print(f"Found actual download URL: {actual_download_url}")

                                # Try the actual download URL directly
                                headers["Referer"] = download_url
                                actual_resp = session.get(actual_download_url, headers=headers, stream=True, allow_redirects=True)

                                if actual_resp.status_code == 200:
                                    content_type = actual_resp.headers.get('content-type', '').lower()
                                    if ('application/zip' in content_type or
                                        'application/octet-stream' in content_type or
                                        'attachment' in actual_resp.headers.get('content-disposition', '')):
                                        print("Direct download from terms page successful!")
                                        resp = actual_resp
                                        break
                                    else:
                                        print(f"Direct download returned content-type: {content_type}")
                                        continue
                                else:
                                    print(f"Direct download failed with status: {actual_resp.status_code}")
                                    continue
                            else:
                                print("Could not extract actual download URL from terms page")
                                continue
                        else:
                            print("Got HTML but doesn't appear to be a terms page")
                            # Save a snippet of the response for debugging
                            snippet = resp.text[:1000] if len(resp.text) > 1000 else resp.text
                            print(f"Response snippet: {snippet}")
                            continue
                    else:
                        print(f"Got non-HTML, non-ZIP content: {content_type}")
                        continue
                else:
                    print(f"HTTP {resp.status_code}")
                    continue
            except Exception as e:
                print(f"Error with {download_url}: {e}")
                continue

        if resp is None or resp.status_code != 200:
            print("All download attempts failed.")
            print(f"Project {pid} may require different permissions or may not be publicly accessible.")
            exit(1)

        # Final validation
        content_type = resp.headers.get('content-type', '').lower()
        if content_type.startswith('text/html'):
            print("Error: Final response was HTML instead of file content.")
            print("This project may not be publicly downloadable or may require special access.")
            exit(1)

        print("Public download successful!")

    else:
        print("Private download method successful!")

    print("Starting download...")

    # Extract filename from Content-Disposition header or create one
    if "Content-Disposition" in resp.headers:
        fname = re.findall("filename=(.+)", resp.headers["Content-Disposition"])[0].strip('"')
    else:
        fname = f"openicpsr-{pid}.zip"

    total_size = int(resp.headers.get('content-length', 0))
    downloaded_size = 0

    print(f"Downloading: {fname}")
    if total_size > 0:
        print(f"Size: {format_bytes(total_size)}")

    spinner = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    spinner_index = 0
    last_update_time = time.time()

    with open(fname, "wb") as fp:
        for chunk in resp.iter_content(chunk_size=8192):
            fp.write(chunk)
            downloaded_size += len(chunk)
            current_time = time.time()

            # Update display every 0.1 seconds
            if (current_time - last_update_time) >= 0.1:
                progress_info = f"Downloaded: {format_bytes(downloaded_size)}"
                if total_size > 0:
                    percentage = (downloaded_size / total_size) * 100
                    progress_info += f" of {format_bytes(total_size)} ({percentage:.1f}%)"
                print(f"{spinner[spinner_index]} {progress_info}", end="\r")
                spinner_index = (spinner_index + 1) % len(spinner)
                last_update_time = current_time

    # Final output
    final_info = f"Downloaded: {format_bytes(downloaded_size)}"
    if total_size > 0:
        final_info += f" of {format_bytes(total_size)}"
    print(f"\n{final_info}")
    print(f"File saved to: {fname}")
    print("Download complete!")