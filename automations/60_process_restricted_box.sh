#!/bin/bash
#set -ev

# 60_process_restricted_box.sh
# Downloads files from the restricted Box folder and runs the 02 manifest
# creation code. This is the script wired into the "8-download-box-manifest"
# Bitbucket pipeline step.
#
# Usage: 60_process_restricted_box.sh [repository_name] [directory] [tag]
#   repository_name - Numeric part of the aearep-NNNN repo name, used to
#                      find the matching subfolder on Box (e.g. 1234 for
#                      aearep-1234). Optional: only used on the name-search
#                      download path; if omitted there, download_box_private.py
#                      auto-detects it from the current directory or git remote.
#   directory        - Directory where restricted data are downloaded to and
#                       read from (defaults to 'restricted').
#   tag              - Optional tag for output files (defaults to directory name).
#
# Environment Variables Required:
#   BOX_FOLDER_PRIVATE    - Box folder ID to download from
#   BOX_PRIVATE_KEY_ID    - Box JWT public key ID
#   BOX_ENTERPRISE_ID     - Box enterprise ID
#   BOX_PRIVATE_JSON      - Base64 encoded Box config JSON (optional, alternative to config file)

repository_name="${1:-}"
directory=${2:-restricted}
tag=${3:-$directory}

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    PYTHON_CMD="python"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "ERROR: No suitable Python installation found"
    exit 1
fi

echo "=== Processing restricted Box folder ==="
echo "Repository: $repository_name"
echo "Directory: $directory"
echo "Tag: $tag"

_jira="${jiraticket:-}"
echo "60_process_restricted_box: jiraticket from environment: '${_jira}'"

if [ -z "$_jira" ]; then
    if [ -f config.yml ] && [ -f tools/parse_yaml.sh ]; then
        . ./tools/parse_yaml.sh
        _jira=$(parse_yaml config.yml | grep '^jiraticket=' | sed 's/jiraticket=//;s/"//g')
        echo "60_process_restricted_box: jiraticket from config.yml: '${_jira}'"
    else
        echo "60_process_restricted_box: config.yml or parse_yaml.sh not found, skipping config.yml lookup"
    fi
fi

if [ -z "$_jira" ]; then
    _icpsr=$(find . -maxdepth 1 -mindepth 1 -type d -name '[123][0-9][0-9][0-9][0-9][0-9]' 2>/dev/null \
             | head -1 | xargs -I{} basename {} 2>/dev/null || true)
    if [ -n "$_icpsr" ]; then
        echo "60_process_restricted_box: detected openICPSR directory '${_icpsr}', looking up Jira ticket"
        _jira=$($PYTHON_CMD tools/jira_find_task_by_icpsr.py "$_icpsr" 2>&1) || true
        echo "60_process_restricted_box: jiraticket from lookup: '${_jira}'"
    else
        echo "60_process_restricted_box: no openICPSR directory found"
    fi
fi

_box_folder_id=""
if [ -n "$_jira" ]; then
    _box_folder_id=$($PYTHON_CMD tools/jira_get_info.py "$_jira" boxfolderid || true)
    echo "60_process_restricted_box: boxfolderid from Jira ${_jira}: '${_box_folder_id}'"
fi

if [ -z "$_box_folder_id" ]; then
    if [ -f config.yml ] && [ -f tools/parse_yaml.sh ]; then
        . ./tools/parse_yaml.sh
        _box_folder_id=$(parse_yaml config.yml | grep '^boxfolderid=' | sed 's/boxfolderid=//;s/"//g')
        echo "60_process_restricted_box: boxfolderid from config.yml: '${_box_folder_id}'"
    else
        echo "60_process_restricted_box: config.yml or parse_yaml.sh not found, skipping config.yml boxfolderid lookup"
    fi
fi

if [ -n "$_box_folder_id" ]; then
    echo "Step 1: Downloading files using known Box folder ID from Jira ($_box_folder_id)..."
    $PYTHON_CMD tools/download_box_private.py --target-folder-id "$_box_folder_id" --output-dir "$directory"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to download files from Box"
        exit 1
    fi
else
    echo "Step 1: Downloading files from restricted Box folder (searching by name)..."
    _download_output=$($PYTHON_CMD tools/download_box_private.py "$repository_name" --output-dir "$directory")
    _download_status=$?
    echo "$_download_output"
    if [ $_download_status -ne 0 ]; then
        echo "ERROR: Failed to download files from Box"
        exit 1
    fi
    _found_folder_id=$(echo "$_download_output" | grep '^BOX_FOLDER_ID=' | tail -1 | cut -d= -f2)
    if [ -n "$_found_folder_id" ] && [ -n "$_jira" ]; then
        echo "60_process_restricted_box: recording discovered Box folder ID '$_found_folder_id' in config.yml"
        if grep -q '^boxfolderid:' config.yml; then
            sed -i "s|^boxfolderid:.*|boxfolderid: ${_found_folder_id}|" config.yml
        else
            echo "boxfolderid: ${_found_folder_id}" >> config.yml
        fi
    fi
fi

file_count=$(find "$directory" -type f | wc -l)
if [ "$file_count" -eq 0 ]; then
    echo "ERROR: No files found in directory '$directory'"
    exit 1
fi

echo "Step 2: Unpacking downloaded files..."
bash automations/00_unpack_zip.sh "$directory"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to unpack files in '$directory'"
    exit 1
fi

echo "Step 3: Running manifest creation..."
bash automations/02_create_manifest.sh "$directory" "$tag"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create manifest for directory '$directory'"
    exit 1
fi

echo "=== Successfully processed restricted data ==="
echo "Directory processed: $directory"
echo "Tag used: $tag"
