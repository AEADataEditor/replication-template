#!/usr/bin/python3
"""
Download artifacts from SIVACOR submission.

This script downloads all artifacts associated with a SIVACOR submission ID,
handles ZIP file extraction, and commits the results to a git branch.

Usage:
    python3 tools/download_sivacor.py [JIRA_CASE]

Examples:
    # Using current directory name as Jira case
    python3 tools/download_sivacor.py

    # Specifying Jira case explicitly
    python3 tools/download_sivacor.py aearep-8885

    # Using config.yml (jiraticket field)
    python3 tools/download_sivacor.py

Arguments:
    JIRA_CASE   - Jira case number (optional)
                  Order of precedence:
                  1. Command line argument
                  2. Current directory name
                  3. config.yml jiraticket field

How it works:
    1. Determines Jira case from argument, directory name, or config.yml
    2. Looks up SIVACOR ID from Jira ticket
    3. Determines target folder from config.yml (precedence: openicpsr > zenodo > dataverse > osf)
    4. Downloads all artifacts using sivacor CLI
    5. If ZIP file exists:
       - Clears folder contents (keeping folder)
       - Unpacks ZIP
       - Downloads other artifacts
    6. Creates branch sivacor-{sivacor_id} (lowercase)
    7. Git adds and commits the folder

Environment Variables Required:
    JIRA_USERNAME - Your Jira email address
    JIRA_API_KEY  - API token from https://id.atlassian.com/manage-profile/security/api-tokens
    SIVACOR environment variables as required by sivacor CLI

Requirements:
    - jira: Python Jira library
    - yaml: YAML configuration file support
    - sivacor: SIVACOR CLI tool (installed via pip)

Error Handling:
    - Exits with error if SIVACOR ID field is not populated in Jira
    - Validates target folder existence
    - Handles missing config.yml gracefully

Authors: Lars Vilhuber
Version: 2026-02-12
"""

import os
import sys
import subprocess
import yaml
import zipfile
import glob
import shutil

version = "2026-02-12"

print(f"SIVACOR downloader v{version}")


def get_jira_case():
    """
    Determine Jira case number.

    Order of precedence:
    1. Command line argument
    2. Current directory name
    3. config.yml jiraticket field

    Returns:
        Jira case number (e.g., 'aearep-8885')
    """
    # Check command line
    if len(sys.argv) >= 2:
        return sys.argv[1].lower()

    # Check current directory name
    current_dir = os.path.basename(os.getcwd())
    if current_dir.startswith('aearep-'):
        return current_dir.lower()

    # Check config.yml
    try:
        with open("config.yml") as f:
            config = next(yaml.load_all(f, Loader=yaml.FullLoader))
            jira_ticket = config.get("jiraticket")
            if jira_ticket:
                return jira_ticket.lower()
    except FileNotFoundError:
        pass

    print("Error: Could not determine Jira case number")
    print(f"Usage: {sys.argv[0]} [JIRA_CASE]")
    print(f"Or run from a directory named aearep-XXXX")
    print(f"Or specify jiraticket in config.yml")
    sys.exit(1)


def get_sivacor_id(jira_case):
    """
    Get SIVACOR ID from Jira using jira_get_info.py

    Args:
        jira_case: Jira case number (e.g., 'aearep-8885')

    Returns:
        SIVACOR ID string
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    jira_script = os.path.join(script_dir, "jira_get_info.py")

    try:
        result = subprocess.run(
            [sys.executable, jira_script, jira_case, "sivacorid"],
            capture_output=True,
            text=True,
            check=False
        )

        sivacor_id = result.stdout.strip()

        if not sivacor_id:
            print(f"Error: SIVACOR ID field is not populated in Jira ticket {jira_case}")
            print(f"Please ensure the 'SIVACOR ID' field is set in the Jira ticket")
            sys.exit(1)

        return sivacor_id

    except Exception as e:
        print(f"Error retrieving SIVACOR ID from Jira: {e}")
        sys.exit(1)


def get_target_folder():
    """
    Get target folder from config.yml

    Precedence: openicpsr > zenodo > dataverse > osf

    Returns:
        Folder name (e.g., '222222')
    """
    try:
        with open("config.yml") as f:
            config = next(yaml.load_all(f, Loader=yaml.FullLoader))

            # Check in order of precedence
            for key in ['openicpsr', 'zenodo', 'dataverse', 'osf']:
                value = config.get(key)
                if value and str(value).strip():
                    return str(value).strip()

            print("Error: No repository folder found in config.yml")
            print("Please specify one of: openicpsr, zenodo, dataverse, or osf")
            sys.exit(1)

    except FileNotFoundError:
        print("Error: config.yml not found")
        sys.exit(1)


def download_sivacor_artifacts(sivacor_id, target_folder):
    """
    Download all artifacts from SIVACOR submission

    Args:
        sivacor_id: SIVACOR submission ID
        target_folder: Target directory for downloads
    """
    print(f"\n{'=' * 60}")
    print(f"Downloading artifacts from SIVACOR ID: {sivacor_id}")
    print(f"Target folder: {target_folder}")
    print(f"{'=' * 60}\n")

    # Create target folder if it doesn't exist
    os.makedirs(target_folder, exist_ok=True)

    # Download all artifacts using sivacor CLI
    # The sivacor CLI downloads to current directory, so we need to cd into target folder
    original_dir = os.getcwd()

    try:
        os.chdir(target_folder)

        print("Downloading all artifacts...")
        result = subprocess.run(
            [sys.executable, "-m", "sivacor", "submission", "get", sivacor_id, "--download", "all"],
            check=True
        )

        os.chdir(original_dir)

    except subprocess.CalledProcessError as e:
        os.chdir(original_dir)
        print(f"Error downloading from SIVACOR: {e}")
        sys.exit(1)


def handle_zip_files(target_folder):
    """
    Handle ZIP file extraction in target folder

    If a ZIP file exists:
    - Clear folder contents (keeping folder)
    - Unpack ZIP
    - Keep other downloaded artifacts

    Args:
        target_folder: Target directory containing downloads
    """
    # Find ZIP files
    zip_files = glob.glob(os.path.join(target_folder, "*.zip"))

    if not zip_files:
        print("No ZIP files found, keeping all downloaded artifacts")
        return

    if len(zip_files) > 1:
        print(f"Warning: Found multiple ZIP files: {zip_files}")
        print(f"Using first ZIP file: {zip_files[0]}")

    zip_file = zip_files[0]
    print(f"\nFound ZIP file: {os.path.basename(zip_file)}")
    print(f"Clearing folder contents and unpacking ZIP...")

    # Get list of all files before clearing
    all_files = [f for f in os.listdir(target_folder) if os.path.isfile(os.path.join(target_folder, f))]
    non_zip_files = [f for f in all_files if not f.endswith('.zip')]

    # Move ZIP to temp location outside the folder
    temp_dir = os.path.dirname(target_folder)
    temp_zip = os.path.join(temp_dir, os.path.basename(zip_file) + ".tmp")
    shutil.move(zip_file, temp_zip)

    # Clear folder contents
    for item in os.listdir(target_folder):
        item_path = os.path.join(target_folder, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)

    # Extract ZIP directly from temp location
    print(f"Extracting ZIP file...")
    try:
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(target_folder)
        print(f"ZIP extracted successfully")

        # Remove the temp ZIP file after extraction
        os.remove(temp_zip)

    except Exception as e:
        print(f"Error extracting ZIP file: {e}")
        # Try to restore the ZIP file if extraction failed
        if os.path.exists(temp_zip):
            shutil.move(temp_zip, zip_file)
        sys.exit(1)

    # Note about other artifacts
    if non_zip_files:
        print(f"Note: Other artifacts were cleared as they may be included in the ZIP")


def git_commit_changes(sivacor_id, target_folder, jira_case):
    """
    Create git branch and commit changes

    Args:
        sivacor_id: SIVACOR submission ID (for branch name)
        target_folder: Folder to git add
        jira_case: Jira case number (for commit message)
    """
    branch_name = f"sivacor-{sivacor_id.lower()}"

    print(f"\n{'=' * 60}")
    print(f"Git operations:")
    print(f"Branch: {branch_name}")
    print(f"{'=' * 60}\n")

    # Check if branch exists
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch_name],
        capture_output=True,
        check=False
    )

    if result.returncode == 0:
        # Branch exists, check it out
        print(f"Branch {branch_name} exists, checking out...")
        subprocess.run(["git", "checkout", branch_name], check=True)
    else:
        # Create new branch
        print(f"Creating new branch {branch_name}...")
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)

    # Git add the folder
    print(f"Adding {target_folder} to git...")
    subprocess.run(["git", "add", target_folder], check=True)

    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        check=False
    )

    if result.returncode == 0:
        print("No changes to commit")
        return

    # Commit
    commit_message = f"[sivacor] Adding artifacts from SIVACOR ID {sivacor_id}"
    print(f"Committing with message: {commit_message}")
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    print(f"\n{'=' * 60}")
    print(f"SUCCESS!")
    print(f"Branch: {branch_name}")
    print(f"Folder: {target_folder}")
    print(f"SIVACOR ID: {sivacor_id}")
    print(f"{'=' * 60}\n")


def main():
    """Main execution function"""

    # Step 1: Determine Jira case
    jira_case = get_jira_case()
    print(f"Jira case: {jira_case}")

    # Step 2: Get SIVACOR ID from Jira
    sivacor_id = get_sivacor_id(jira_case)
    print(f"SIVACOR ID: {sivacor_id}")

    # Step 3: Get target folder from config.yml
    target_folder = get_target_folder()
    print(f"Target folder: {target_folder}")

    # Step 4: Download artifacts
    download_sivacor_artifacts(sivacor_id, target_folder)

    # Step 5: Handle ZIP files
    handle_zip_files(target_folder)

    # Step 6: Git operations
    git_commit_changes(sivacor_id, target_folder, jira_case)


if __name__ == '__main__':
    main()
