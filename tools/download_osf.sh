#!/bin/bash
#
# Download files from Open Science Framework (OSF) projects
#
# This script downloads all files and directories from an OSF project using the
# osfclient command-line tool. It's designed for replication workflows where
# researchers need to download datasets, code, and other materials from OSF
# repositories for analysis and verification.
#
# Usage:
#   ./download_osf.sh <OSF_DOI_OR_PROJECT_ID>
#   bash tools/download_osf.sh <OSF_DOI_OR_PROJECT_ID>
#
# Examples:
#   # Using project ID directly
#   ./download_osf.sh abc12
#
#   # Using full OSF URL
#   ./download_osf.sh https://osf.io/abc12/
#
#   # Using OSF DOI
#   ./download_osf.sh 10.17605/OSF.IO/ABC12
#
# Arguments:
#   OSF_DOI_OR_PROJECT_ID  - OSF project identifier, can be:
#                           - Project ID (e.g., "abc12")
#                           - Full OSF URL (e.g., "https://osf.io/abc12/")
#                           - OSF DOI (e.g., "10.17605/OSF.IO/ABC12")
#
# Requirements:
#   - osfclient: OSF command-line client (pip install osfclient)
#   - Internet connection to access OSF API
#   - Read/write permissions in current directory
#
# Features:
#   - Flexible input parsing (accepts URLs, DOIs, or project IDs)
#   - Creates organized directory structure: osf-[PROJECT_ID]
#   - Downloads complete project structure including subdirectories
#   - Preserves original file organization and metadata
#   - Validates osfclient installation before proceeding
#
# Behavior:
#   - Extracts project ID from various input formats
#   - Creates target directory named "osf-[PROJECT_ID]"
#   - Downloads all files using osfclient's clone command
#   - Maintains original directory structure from OSF
#   - Exits with error if osfclient is not installed
#
# Output Structure:
#   Input: abc12 (or https://osf.io/abc12/ or DOI)
#   Output directory: ./osf-abc12/
#   Contents: All files and folders from the OSF project
#
# Error Handling:
#   - Checks for osfclient installation
#   - Validates command-line arguments
#   - Reports download failures from osfclient
#
# Dependencies:
#   osfclient installation:
#   - pip install osfclient
#   - or pip install -r requirements.txt (if included in project requirements)
#
# OSF API:
#   - Uses osfclient which interfaces with OSF's REST API
#   - Supports public projects (no authentication required for public data)
#   - For private projects, authentication setup may be required
#
# Note: This script is designed for downloading public OSF projects.
# For private projects, you may need to configure osfclient authentication
# following the osfclient documentation.
#
# See also:
#   - OSF documentation: https://help.osf.io/
#   - osfclient documentation: https://github.com/osfclient/osfclient
#


# Function to check if osfclient is installed
check_osfclient_installed() {
    if ! command -v osf &> /dev/null; then
        echo "osfclient is not installed. Please ensure it is installed, using `pip install -r requirements.txt`."
        exit 1
    fi
}

# Function to parse the project ID from the DOI or project ID
parse_project_id() {
    local input=$1
    if [[ $input == *"/"* ]]; then
        project_id=$(echo $input | awk -F'/' '{print $NF}')
    else
        project_id=$input
    fi
}

# Main script
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <OSF DOI or Project ID>"
    exit 1
fi

input=$1
parse_project_id $input
check_osfclient_installed

# Create directory with the project ID, prepended by 'osf-'
dir_name="osf-$project_id"
mkdir -p $dir_name

# Clone the project into the directory
cd $dir_name
osf -p $project_id clone 
