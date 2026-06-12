#!/bin/bash
#set -ev

# 60_process_restricted_box.sh
# Downloads files from the restricted Box folder and runs the 04 code with specified tag
# This script relies on environment variables for Box authentication

# Set defaults
directory=${1:-restricted}
tag=$2

# Detect OS and set appropriate Python command
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash)
    PYTHON_CMD="python"
elif command -v python3.12 &> /dev/null; then
    # Linux/macOS with python3.12 available
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    # Linux/macOS with python3 available
    PYTHON_CMD="python3"
else
    echo "ERROR: No suitable Python installation found"
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"

cat << EOF
$0 [(directory)] [(tag)]

Downloads files from restricted Box folder and runs the 04 manifest creation code.

Arguments:
  directory    - Directory where restricted data are present (defaults to 'restricted')
  tag          - Optional tag for output files (defaults to directory name)

Environment Variables Required:
  BOX_FOLDER_PRIVATE    - Box folder ID to download from
  BOX_PRIVATE_KEY_ID    - Box JWT public key ID  
  BOX_ENTERPRISE_ID     - Box enterprise ID
  BOX_OUTPUT_DIR        - Directory to download files to (used by download script)
  BOX_PRIVATE_JSON      - Base64 encoded Box config JSON (optional, alternative to config file)

Examples:
  $0                           # Uses 'restricted' directory and tag
  $0 restricted confidential   # Uses 'restricted' directory with 'confidential' tag
  $0 mydata                    # Uses 'mydata' directory and tag

EOF

echo "=== Processing restricted Box folder ==="
echo "Directory: $directory"
echo "Tag: ${tag:-$directory}"

# Step 1: Download files from restricted Box folder (if we have environment to do so)
if [ ! -z "$BOX_FOLDER_PRIVATE" ]; then
    echo "Step 1: Downloading files from restricted Box folder..."
    # Extract numeric part from directory name for subfolder argument
    $PYTHON_CMD tools/download_box_private.py
        
      # Check if download was successful
      if [ $? -ne 0 ]; then
          echo "ERROR: Failed to download files from Box"
          exit 1
      fi
    
else
    echo "Step 1: Skipping download (BOX_FOLDER_PRIVATE not set)"
    exit 2
fi

# Verify that the directory exists and contains files
if [ ! -d "$directory" ]; then
    echo "ERROR: Directory '$directory' does not exist"
    exit 1
fi

file_count=$(find "$directory" -type f | wc -l)
if [ "$file_count" -eq 0 ]; then
    echo "ERROR: No files found in directory '$directory'"
    exit 1
fi

echo "Found $file_count files in '$directory'"

# Step 2: Run the 04 manifest creation code
echo "Step 2: Running manifest creation..."
bash automations/04_create_manifest.sh "$directory" "$tag"

# Check if manifest creation was successful
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create manifest for directory '$directory'"
    exit 1
fi

echo "=== Successfully processed restricted data ==="
echo "Directory processed: $directory"
echo "Tag used: ${tag:-$directory}"