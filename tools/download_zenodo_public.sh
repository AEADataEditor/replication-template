#!/bin/bash
#
# Download files from public Zenodo repositories
#
# This script downloads all files from a public Zenodo record using the zenodo_get
# command-line tool. It's designed for replication workflows where researchers need
# to download published datasets, code, and supplementary materials from Zenodo
# repositories for analysis and verification.
#
# Usage:
#   ./download_zenodo_public.sh <RECORD_ID>
#   bash tools/download_zenodo_public.sh <RECORD_ID>
#
# Examples:
#   # Using Zenodo record ID
#   ./download_zenodo_public.sh 1234567
#
#   # Using full Zenodo URL (script extracts ID automatically)
#   ./download_zenodo_public.sh https://zenodo.org/record/1234567
#
#   # Using Zenodo DOI (script extracts ID automatically)
#   ./download_zenodo_public.sh 10.5281/zenodo.1234567
#
# Arguments:
#   RECORD_ID  - Zenodo record identifier, can be:
#              - Numeric record ID (e.g., "1234567")
#              - Full Zenodo URL (e.g., "https://zenodo.org/record/1234567")
#              - Zenodo DOI (e.g., "10.5281/zenodo.1234567")
#
# Requirements:
#   - zenodo_get: Zenodo command-line client (pip install zenodo_get)
#   - Internet connection to access Zenodo API
#   - Read/write permissions in current directory
#
# Features:
#   - Flexible input parsing (extracts record ID from URLs and DOIs)
#   - Creates organized directory structure: zenodo-[RECORD_ID]
#   - Downloads all files from the specified Zenodo record
#   - Prevents overwriting existing downloads
#   - Simple error handling and validation
#
# Behavior:
#   - Parses input to extract Zenodo record ID
#   - Creates target directory named "zenodo-[RECORD_ID]"
#   - Checks if directory already exists (prevents accidental overwrites)
#   - Downloads all files using zenodo_get tool
#   - Maintains original file names and organization
#
# Output Structure:
#   Input: 1234567 (or https://zenodo.org/record/1234567)
#   Output directory: ./zenodo-1234567/
#   Contents: All files from the Zenodo record
#
# Error Handling:
#   - Validates command-line arguments (requires exactly one argument)
#   - Checks for existing output directory
#   - Reports download failures from zenodo_get
#   - Exits with error code 2 on validation failures
#
# Dependencies:
#   zenodo_get installation:
#   - pip install zenodo_get
#   - or pip install -r requirements.txt (if included in project requirements)
#
# Zenodo API:
#   - Uses zenodo_get which interfaces with Zenodo's REST API
#   - Works with public records (no authentication required)
#   - Supports both published and pre-published public records
#
# Input Format Handling:
#   - Automatically extracts record ID from various input formats
#   - For URLs/DOIs: extracts numeric ID from the end
#   - For direct IDs: uses as-is (supports both old 7-digit and new 8+ digit IDs)
#   - Examples:
#     * "12345678" → "12345678"
#     * "https://zenodo.org/record/12345678" → "12345678"  
#     * "10.5281/zenodo.12345678" → "12345678"
#     * "https://zenodo.org/doi/10.5281/zenodo.12345678" → "12345678"
#
# Note: This script is designed for downloading public Zenodo records only.
# For private or restricted records, use the download_zenodo_draft.py script
# which supports authentication.
#
# See also:
#   - Zenodo documentation: https://help.zenodo.org/
#   - zenodo_get documentation: https://github.com/dvolgyes/zenodo_get
#

# Function to find available Python interpreter
find_python() {
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        echo "ERROR: No Python interpreter found. Please install Python." >&2
        exit 1
    fi
}

# Function to check and install zenodo_get if needed
check_zenodo_get() {
    local python_cmd=$1
    
    if ! $python_cmd -c "import zenodo_get" &> /dev/null; then
        echo "zenodo_get module not found. Installing..."
        if $python_cmd -m pip install zenodo_get; then
            echo "zenodo_get installed successfully"
        else
            echo "ERROR: Failed to install zenodo_get. Please install manually:" >&2
            echo "  $python_cmd -m pip install zenodo_get" >&2
            exit 1
        fi
    fi
}

# Function to extract Zenodo record ID from various input formats
extract_record_id() {
    local input=$1
    local record_id
    
    # Remove any trailing slashes
    input=${input%/}
    
    # Handle different input formats
    if [[ $input =~ ^[0-9]+$ ]]; then
        # Direct numeric ID
        record_id=$input
    elif [[ $input == *"zenodo.org"* ]]; then
        # Extract from Zenodo URLs (various formats)
        if [[ $input =~ /([0-9]+)$ ]]; then
            record_id=${BASH_REMATCH[1]}
        elif [[ $input =~ zenodo\.([0-9]+) ]]; then
            record_id=${BASH_REMATCH[1]}
        fi
    elif [[ $input == *"zenodo."* ]]; then
        # Extract from DOI format (10.5281/zenodo.12345678)
        if [[ $input =~ zenodo\.([0-9]+) ]]; then
            record_id=${BASH_REMATCH[1]}
        fi
    else
        # Fallback: try to extract any number at the end
        if [[ $input =~ ([0-9]+)$ ]]; then
            record_id=${BASH_REMATCH[1]}
        fi
    fi
    
    if [[ -z $record_id ]]; then
        echo "ERROR: Could not extract Zenodo record ID from: $input" >&2
        echo "Expected formats:" >&2
        echo "  - Record ID: 12345678" >&2
        echo "  - Zenodo URL: https://zenodo.org/record/12345678" >&2
        echo "  - Zenodo DOI: 10.5281/zenodo.12345678" >&2
        exit 1
    fi
    
    echo $record_id
}

python=$(find_python)

# Check and install zenodo_get if needed
check_zenodo_get $python

if [[ -z $1 ]]
then
  cat << EOF
Usage: $0 <RECORD_ID>

Downloads all files from a public Zenodo record.

Arguments:
  RECORD_ID    Zenodo record identifier, can be:
               - Record ID: 12345678
               - Zenodo URL: https://zenodo.org/record/12345678
               - Zenodo DOI: 10.5281/zenodo.12345678

Examples:
  $0 12345678
  $0 https://zenodo.org/record/12345678
  $0 10.5281/zenodo.12345678

EOF
exit 2
fi

# Extract record ID from input
projectID=$(extract_record_id "$1")

echo "Zenodo Record ID: $projectID"

# Test if directory exists
#

zenodo_dir=zenodo-$projectID

if [ -d $zenodo_dir ]
then
	echo "$zenodo_dir already exists - please remove prior to downloading"
	exit 2
fi

echo "Downloading Zenodo record $projectID to $zenodo_dir..."

# Use zenodo_get_ci.py wrapper which handles CI detection and progress bar suppression
$python tools/zenodo_get_ci.py --output-dir=$zenodo_dir $projectID

if [ $? -eq 0 ]; then
    echo "Download completed successfully!"
    echo "Files downloaded to: $zenodo_dir"
else
    echo "ERROR: Download failed" >&2
    exit 1
fi
