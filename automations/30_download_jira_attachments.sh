#!/bin/bash
#
# Download Jira attachments for the current case
#
# Usage: bash automations/30_download_jira_attachments.sh [--list] [--filter PATTERN]
#
# Reads the Jira ticket from config.yml and downloads all attachments
# to the repository root directory with their original filenames.
#
# Options:
#   --list              List attachments without downloading
#   --filter PATTERN    Only download files matching PATTERN (e.g., ".pdf", "manuscript")
#
# Environment:
#   JIRA_USERNAME   - Jira email address (required)
#   JIRA_API_KEY    - Jira API token (required)
#
# Examples:
#   bash automations/30_download_jira_attachments.sh
#   bash automations/30_download_jira_attachments.sh --list
#   bash automations/30_download_jira_attachments.sh --filter manuscript
#   bash automations/30_download_jira_attachments.sh --filter form

set -e

# Get script directory and repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Parse command line arguments
LIST_ONLY=""
FILTER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --list|-l)
            LIST_ONLY="true"
            shift
            ;;
        --filter|-f)
            FILTER="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--list] [--filter PATTERN]"
            echo ""
            echo "Download Jira attachments for the current case."
            echo ""
            echo "Options:"
            echo "  --list              List attachments without downloading"
            echo "  --filter PATTERN    Only download files matching PATTERN"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --list"
            echo "  $0 --filter manuscript"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Check for required environment variables
if [[ -z "${JIRA_USERNAME}" || -z "${JIRA_API_KEY}" ]]; then
    echo "Error: JIRA_USERNAME and JIRA_API_KEY environment variables must be set" >&2
    echo "Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens" >&2
    exit 1
fi

# Read Jira ticket from config.yml
CONFIG_FILE="${REPO_ROOT}/config.yml"

if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "Error: config.yml not found at ${CONFIG_FILE}" >&2
    exit 1
fi

# Extract jiraticket value from config.yml
JIRA_TICKET=$(grep "^jiraticket:" "${CONFIG_FILE}" | awk '{print $2}' | tr -d ' ')

if [[ -z "${JIRA_TICKET}" ]]; then
    echo "Error: jiraticket not found in config.yml" >&2
    exit 1
fi

echo "Jira ticket: ${JIRA_TICKET}"
echo ""

# Build arguments array for Python script
ARGS=("${JIRA_TICKET}" --output-dir "${REPO_ROOT}" --verbose)
[[ -n "${LIST_ONLY}" ]] && ARGS+=(--list)
[[ -n "${FILTER}" ]] && ARGS+=(--filter "${FILTER}")

# Run the Python script
cd "${REPO_ROOT}"
python3 "${REPO_ROOT}/tools/jira_download_attachments.py" "${ARGS[@]}"
