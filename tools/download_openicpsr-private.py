#!/usr/bin/python3
"""
Download files from private (unpublished) openICPSR deposits.

This script authenticates with openICPSR and downloads all files from a private deposit
as a ZIP archive, then extracts it to a local directory. It's designed for downloading
draft/unpublished deposits that require authentication and are not publicly accessible.

Usage:
    python3 tools/download_openicpsr-private.py PROJECT_ID [path] [login]

Examples:
    # Using environment variables for authentication
    export ICPSR_EMAIL="your.email@domain.com"
    export ICPSR_PASS="your_password"
    python3 tools/download_openicpsr-private.py 123456

    # Specifying download path
    python3 tools/download_openicpsr-private.py 123456 ./downloads

    # Interactive login (will prompt for password)
    python3 tools/download_openicpsr-private.py 123456 ./downloads your.email@domain.com

    # Using config file (config.yml with openicpsr: PROJECT_ID)
    python3 tools/download_openicpsr-private.py

Arguments:
    PROJECT_ID  - Numeric openICPSR project ID (required, must be digits only)
    path        - Download directory (optional, default: current directory)
    login       - Email for interactive authentication (optional, will prompt for password)

Authentication Methods (in order of preference):
    1. Command line login + interactive password prompt
    2. Environment variables: ICPSR_EMAIL and ICPSR_PASS
    3. Config file: config.yml with 'openicpsr: PROJECT_ID'

Environment Variables:
    ICPSR_EMAIL - Your openICPSR account email
    ICPSR_PASS  - Your openICPSR account password
    ICPSR_TOKEN - Optional Cloudflare bypass token (added to x-openicpsr-cloudflare-token header)
    DEBUG       - Enable debug output (any non-empty value)
    CI          - Indicates CI environment for automatic git operations

Features:
    - OAuth-based authentication with openICPSR
    - Downloads entire deposit as ZIP archive
    - Extracts files to directory named after project ID
    - Progress indicator with download size tracking
    - Automatic git integration in CI environments
    - Skips extraction if target directory already exists
    - Validates project ID format (must be numeric)

Output:
    - Downloads ZIP file to specified path
    - Extracts contents to subdirectory named PROJECT_ID
    - In CI environments: automatically commits extracted files to git

Requirements:
    - requests: HTTP client library
    - yaml: YAML configuration file support
    - Valid openICPSR account with access to the specified deposit

Security Notes:
    - Credentials are handled securely (no logging of passwords)
    - Uses session-based authentication
    - Supports both environment variable and interactive password input

Error Handling:
    - Validates project ID format
    - Checks authentication success
    - Verifies download completion
    - Handles missing dependencies gracefully

Note: This tool is for downloading private/draft deposits. For published deposits,
consider using the standard openICPSR public download mechanisms.

Authors: Kacper Kowalik (xarthisius), Lars Vilhuber
Version: 2025-12-15
"""

# Tool to download from unpublished (private) openICPSR deposit
# Provided by Kacper Kowalik (xarthisius)
import getpass
import os
import platform
import re
import socket
import subprocess
import sys
import time
import zipfile

import requests
import yaml

version = "2025-12-15"

print(f"openICPSR downloader v{version}")

# Track download start time
download_start_time = time.time()

def get_system_info():
    """Get system information (cross-platform)."""
    info = {}

    try:
        # Get hostname
        info['hostname'] = socket.gethostname()
    except Exception:
        pass

    try:
        # Get local IP address (works on most platforms)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info['local_ip'] = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    try:
        # Get public IP address with timeout
        response = requests.get('https://api.ipify.org?format=text', timeout=0.5)
        if response.status_code == 200:
            info['public_ip'] = response.text.strip()
    except Exception:
        # Gracefully fail if we can't get public IP
        pass

    return info

def print_system_info(info):
    """Print system information if available."""
    if not info:
        return

    print(f"\n{'=' * 60}")
    print("System Information:")
    if 'hostname' in info:
        print(f"  Hostname:   {info['hostname']}")
    if 'local_ip' in info:
        print(f"  Local IP:   {info['local_ip']}")
    if 'public_ip' in info:
        print(f"  Public IP:  {info['public_ip']}")
    if 'token_used' in info:
        print(f"  Cloudflare Token Used: {info['token_used']}")
    print(f"{'=' * 60}")

def print_download_summary(download_time, download_size_bytes, output_files):
    """Print ASCII art box with download summary"""
    download_size_gb = download_size_bytes / (1024 ** 3)
    minutes = int(download_time // 60)
    seconds = download_time % 60

    # Truncate output files to first 5
    if len(output_files) > 5:
        files_display = output_files[:5] + [f"... and {len(output_files) - 5} more files"]
    else:
        files_display = output_files

    # Create the ASCII art box
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 20 + "DOWNLOAD COMPLETE" + " " * 21 + "║")
    print("╠" + "═" * 58 + "╣")
    print(f"║ Size: {download_size_gb:.3f} GB" + " " * (47 - len(f"Size: {download_size_gb:.3f} GB")) + "║")
    if minutes > 0:
        time_str = f"Time: {minutes}m {seconds:.1f}s"
    else:
        time_str = f"Time: {seconds:.1f}s"
    print(f"║ {time_str}" + " " * (56 - len(time_str)) + "║")
    print("╠" + "═" * 58 + "╣")
    print("║ Output files:" + " " * 45 + "║")
    for file in files_display:
        file_line = f"  • {file}"
        if len(file_line) > 56:
            file_line = file_line[:53] + "..."
        print(f"║ {file_line}" + " " * (56 - len(file_line)) + "║")
    print("╚" + "═" * 58 + "╝")

# ============================
# Environment vars part
# ============================
OPENICPSR_URL = "https://www.openicpsr.org/openicpsr/"
# For info only
OPENICPSR_DEPOSITOR_BASE = OPENICPSR_URL + "workspace?goToPath=/openicpsr"
mypassword = os.environ.get("ICPSR_PASS")
mylogin = os.environ.get("ICPSR_EMAIL")
icpsr_token = os.environ.get("ICPSR_TOKEN")
debug = os.environ.get("DEBUG")
savepath = "."

if debug:
    print("Debug turned on")
else:
    print("No debug:" + str(debug))
# get pid from config file:
pid = None
try:
    with open("config.yml") as f:
        config = next(yaml.load_all(f, Loader=yaml.FullLoader))
        pid = config["openicpsr"]
except FileNotFoundError:
    print("No config file found")

# ============================

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

# Add ICPSR_TOKEN to headers if available
if icpsr_token:
    headers["x-openicpsr-cloudflare-token"] = icpsr_token


# parse command line overrides
if len(sys.argv) >= 2:
    pid = sys.argv[1]
    # Validate and clean project ID
    pid = pid.rstrip('/')  # Remove trailing slash
    if not pid.isdigit():
        print(f"Error: Project ID must be numeric. Got '{pid}'")
        print(f"Example: 12345")
        print(f"Usage: {sys.argv[0]} <PROJECT ID> [path] [login]")
        exit(1)
if len(sys.argv) >= 3:
    savepath = sys.argv[2]
if len(sys.argv) >= 4:
    mylogin = sys.argv[3]
    # if we are provided a login, we prompt for the password
    print(f"===========================================")
    print(f"Project ID: {pid}")
    print(f"Path      : {savepath}")
    print(f"Login     : {mylogin}")
    mypassword = getpass.getpass()

# Final validation of project ID
if pid is None:
    print("Error: No project ID provided")
    print(f"Please provide project ID via:")
    print(f"  1. Command line: {sys.argv[0]} <PROJECT ID> [path] [login]")
    print(f"  2. Config file: config.yml with 'openicpsr: PROJECT_ID'")
    exit(1)

# Validate project ID format (must be numeric)
pid_str = str(pid).rstrip('/')  # Remove trailing slash and convert to string
if not pid_str.isdigit():
    print(f"Error: Project ID must be numeric. Got '{pid_str}'")
    print(f"Example: 12345")
    print(f"Usage: {sys.argv[0]} <PROJECT ID> [path] [login]")
    exit(1)

pid = pid_str  # Use the cleaned version


if mypassword is None or len(mypassword) == 0:
    print(f"Password must be passed via ENV")
    print(f"or by specifying a login as arg3, then prompt for password")
    exit()

if debug == 1:
    print(len(sys.argv))
    print(str(sys.argv))

# Display system information (Linux only)
system_info = get_system_info()
system_info['token_used'] = 'TRUE' if icpsr_token else 'FALSE'
print_system_info(system_info)

# Display deposit information before starting download
print(f"\n{'=' * 60}")
print(f"Starting download for openICPSR deposit: {pid}")
print(f"Save path: {savepath}")
print(f"{'=' * 60}\n")

with requests.Session() as session:
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
        f"{OPENICPSR_URL}/login",
        headers=headers,
        allow_redirects=True,
    )
    login_req.raise_for_status()

    action_url_pattern = r'action="([^"]*)"'
    matches = re.findall(action_url_pattern, login_req.text)
    action_url = matches[0] if matches else None

    data = {
        "username": mylogin,
        "password": mypassword,
    }
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    print("Logging in...")
    req = session.post(
        action_url,
        headers=headers,
        data=data,
        allow_redirects=True,
    )
    req.raise_for_status()
    headers.pop("Content-Type")

    print("Accessing files...")
    data_url = (
        f"https://deposit.icpsr.umich.edu/deposit/downloadZip?dirPath=/openicpsr/{pid}"
    )

    print("Getting file info...")
    resp = session.get(data_url, headers=headers, allow_redirects=True, stream=True)
    if resp.status_code == 200:
        # Extract filename from Content-Disposition header or URL
        if "Content-Disposition" in resp.headers:
            filename = re.findall("filename=(.+)", resp.headers["Content-Disposition"])[
                0
            ].strip('"')
        else:
            filename = f"icpsr-{pid}.zip"
        print(f"Downloading file: {filename}")
        def format_bytes(bytes_val):
            """Format bytes into human readable format with 2 decimal places."""
            if bytes_val < 1024:
                return f"{bytes_val} B"
            elif bytes_val < 1024**2:
                return f"{bytes_val/1024:.2f} KB"
            elif bytes_val < 1024**3:
                return f"{bytes_val/(1024**2):.2f} MB"
            else:
                return f"{bytes_val/(1024**3):.2f} GB"
        
        outfile = f"{savepath}/{filename}"
        total_size = int(resp.headers.get('content-length', 0))
        downloaded_size = 0
        download_size_bytes = 0
        is_ci = os.getenv("CI")
        spinner = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']  # Braille block spinner animation frames
        spinner_index = 0
        last_update_time = time.time()
        last_line_length = 0  # Track length of last printed line for proper clearing
        with open(outfile, "wb") as file:
            for chunk in resp.iter_content(chunk_size=4096):
                file.write(chunk)
                downloaded_size += len(chunk)
                download_size_bytes += len(chunk)
                current_time = time.time()

                # Update display every 0.3 seconds for slower animation
                if (current_time - last_update_time) >= 0.3:
                    if not is_ci:
                        progress_info = f"Downloaded: {format_bytes(downloaded_size)}"
                        if total_size > 0:
                            progress_info += f" of {format_bytes(total_size)}"
                        line = f"{spinner[spinner_index]} {progress_info}"
                        # Clear previous line by overwriting with spaces
                        print(f"\r{' ' * last_line_length}\r{line}", end="", flush=True)
                        last_line_length = len(line)
                    spinner_index = (spinner_index + 1) % len(spinner)
                    last_update_time = current_time
        # Clear the spinner line completely before printing final info
        if not is_ci:
            print(f"\r{' ' * last_line_length}\r", end="")
        final_info = f"Downloaded: {format_bytes(downloaded_size)}"
        if total_size > 0:
            final_info += f" of {format_bytes(total_size)}"
        print(final_info)
    else:
        print(f"Failed to download ZIP file. Status code: {resp.status_code}")
        print(f"Verify that the project ID is correct, and that authentication works.")
        print(f" {OPENICPSR_DEPOSITOR_BASE}/{pid}&goToLevel=project")
        quit(2)



# in principle, we should now have a file

try:
    with zipfile.ZipFile(outfile) as z:
        print("File downloaded " + outfile)
        # here we check if the directory already exists.
        # If it does, then we don't do anything.
        if os.path.exists(f"{savepath}/{pid}"):
            print(f"Directory already exists, doing nothing")
            # Still calculate and show summary for existing directory
            output_files = []
            for root, dirs, files in os.walk(f"{savepath}/{pid}"):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), f"{savepath}/{pid}")
                    output_files.append(rel_path)
            download_time = time.time() - download_start_time
            print_download_summary(download_time, os.path.getsize(outfile), output_files)
            quit()
        # if it does not, we extract in the standard path
        z.extractall(path=str(pid))
        
        # Collect extracted files for summary
        output_files = []
        for root, dirs, files in os.walk(str(pid)):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), str(pid))
                output_files.append(rel_path)
                
except FileNotFoundError:
    print("No downloaded file found")
    print("Something went wrong")
    quit(2)

# Now git add the directory, if we are in CI

if os.getenv("CI"):
    # we are on a pipeline/action
    os.system("git add -v " + str(pid))
    os.system(
        "git commit -m '[skip ci] Adding files from openICPSR project "
        + str(pid)
        + "' "
        + str(pid)
    )
else:
    print("You may want to 'git add' the contents of " + str(pid))

# Print download summary
download_time = time.time() - download_start_time
print_download_summary(download_time, download_size_bytes, output_files)
