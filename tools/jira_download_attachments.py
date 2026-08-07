#!/usr/bin/env python3
"""
Download attachments from a Jira issue.

Downloads all attachments from the specified Jira issue and saves them with their
original filenames to the specified directory (defaults to current directory).

Usage:
    python3 jira_download_attachments.py <issue-key> [--output-dir DIR] [--filter PATTERN]
    python3 jira_download_attachments.py -h|--help

Arguments:
    issue-key       Jira issue key (e.g., AEAREP-9354, aearep-9354)

Options:
    --output-dir DIR    Directory to save attachments (default: current directory)
    --filter PATTERN    Only download files matching this pattern (case-insensitive substring match)
                       Examples: --filter ".pdf" or --filter "manuscript"
    --list             List attachments without downloading
    --verbose          Print detailed progress information

Examples:
    # Download all attachments from AEAREP-9354 to current directory
    python3 jira_download_attachments.py AEAREP-9354

    # Download to specific directory
    python3 jira_download_attachments.py AEAREP-9354 --output-dir ./attachments

    # Download only PDF files
    python3 jira_download_attachments.py AEAREP-9354 --filter ".pdf"

    # Download only files with "manuscript" or "form" in the name
    python3 jira_download_attachments.py AEAREP-9354 --filter "manuscript"
    python3 jira_download_attachments.py AEAREP-9354 --filter "form"

    # List attachments without downloading
    python3 jira_download_attachments.py AEAREP-9354 --list

Environment Variables Required:
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens

    To obtain a JIRA API token:
    1. Visit https://id.atlassian.com/manage-profile/security/api-tokens
    2. Click "Create API token"
    3. Copy the token and set it as JIRA_API_KEY environment variable

Output:
    Downloads attachments to the specified directory
    Prints the filename of each downloaded attachment
    Exit code 0 on success, 1 on error

Error Handling:
    - Missing credentials: Prints error and exits with code 1
    - Invalid issue key: Prints error and exits with code 1
    - Network errors: Prints error and exits with code 1
    - No attachments found: Prints warning and exits with code 0
"""

import argparse
import os
import sys
from pathlib import Path
from jira import JIRA


def get_jira_client():
    """Initialize and return authenticated Jira client."""
    jira_username = os.environ.get('JIRA_USERNAME')
    jira_api_key = os.environ.get('JIRA_API_KEY')

    if not jira_username or not jira_api_key:
        print("Error: JIRA_USERNAME and JIRA_API_KEY environment variables must be set", file=sys.stderr)
        print("Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens", file=sys.stderr)
        return None

    jira_url = "https://aeadataeditors.atlassian.net"

    try:
        jira = JIRA(
            server=jira_url,
            basic_auth=(jira_username, jira_api_key),
            options={'verify': True}
        )
        return jira
    except Exception as e:
        print(f"Error: Failed to connect to Jira: {e}", file=sys.stderr)
        return None


def list_attachments(issue_key, verbose=False):
    """List all attachments for a Jira issue."""
    jira = get_jira_client()
    if not jira:
        return []

    issue_key = issue_key.upper()
    
    try:
        issue = jira.issue(issue_key)
    except Exception as e:
        print(f"Error: Failed to fetch issue {issue_key}: {e}", file=sys.stderr)
        return []

    attachments = issue.fields.attachment
    
    if verbose:
        print(f"Found {len(attachments)} attachment(s) for {issue_key}:", file=sys.stderr)
    
    attachment_info = []
    for attachment in attachments:
        size_kb = attachment.size / 1024
        attachment_info.append({
            'filename': attachment.filename,
            'size': attachment.size,
            'content': attachment.content,
            'id': attachment.id
        })
        if verbose:
            print(f"  - {attachment.filename} ({size_kb:.1f} KB)", file=sys.stderr)
    
    return attachment_info


def download_attachments(issue_key, output_dir=".", filter_pattern=None, verbose=False, list_only=False):
    """
    Download all attachments from a Jira issue.
    
    Args:
        issue_key: Jira issue key (e.g., "AEAREP-9354")
        output_dir: Directory to save attachments (default: current directory)
        filter_pattern: Only download files matching this pattern (case-insensitive)
        verbose: Print detailed progress information
        list_only: Only list attachments without downloading
    
    Returns:
        List of downloaded filenames (or all filenames if list_only=True)
    """
    attachments = list_attachments(issue_key, verbose=verbose)
    
    if not attachments:
        print(f"No attachments found for {issue_key}", file=sys.stderr)
        return []
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    if not list_only:
        output_path.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = []
    
    for attachment in attachments:
        filename = attachment['filename']
        
        # Apply filter if specified
        if filter_pattern and filter_pattern.lower() not in filename.lower():
            if verbose:
                print(f"Skipping {filename} (does not match filter)", file=sys.stderr)
            continue
        
        if list_only:
            print(f"{filename} ({attachment['size']} bytes)")
            downloaded_files.append(filename)
            continue
        
        # Download the attachment
        try:
            jira = get_jira_client()
            if not jira:
                return downloaded_files
            
            # Get the attachment content
            response = jira._session.get(attachment['content'])
            response.raise_for_status()
            
            # Save to file
            output_file = output_path / filename
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded: {filename}")
            downloaded_files.append(filename)
            
        except Exception as e:
            print(f"Error: Failed to download {filename}: {e}", file=sys.stderr)
    
    if not list_only and downloaded_files:
        print(f"\nSuccessfully downloaded {len(downloaded_files)} file(s) to {output_path.absolute()}", file=sys.stderr)
    
    return downloaded_files


def main():
    parser = argparse.ArgumentParser(
        description='Download attachments from a Jira issue',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('Usage:')[0].strip()
    )
    
    parser.add_argument('issue_key', 
                       help='Jira issue key (e.g., AEAREP-9354)')
    parser.add_argument('--output-dir', '-o', 
                       default='.',
                       help='Directory to save attachments (default: current directory)')
    parser.add_argument('--filter', '-f',
                       default=None,
                       help='Only download files matching this pattern (case-insensitive substring)')
    parser.add_argument('--list', '-l',
                       action='store_true',
                       help='List attachments without downloading')
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Print detailed progress information')
    
    args = parser.parse_args()
    
    # Download attachments
    downloaded = download_attachments(
        args.issue_key,
        output_dir=args.output_dir,
        filter_pattern=args.filter,
        verbose=args.verbose,
        list_only=args.list
    )
    
    if not downloaded and not args.list:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
