#!/bin/bash

# sync-codeocean.sh - Synchronize CodeOcean capsules with local repositories
#
# DESCRIPTION:
#   This script manages synchronization between CodeOcean capsules and local
#   Git repositories. It maintains both a live Git clone and a static copy
#   of a CodeOcean capsule, keeping them synchronized with the remote capsule.
#
# USAGE:
#   ./sync-codeocean.sh <codeocean-number>
#
# PARAMETERS:
#   codeocean-number  - The numeric ID of the CodeOcean capsule to sync
#
# WORKFLOW:
#   1. Creates or updates a live Git clone from CodeOcean (codeocean-{number}-live)
#   2. Creates or updates a static copy without Git metadata (codeocean-{number})
#   3. Synchronizes changes from the live clone to the static copy
#   4. Stages changes in the current Git repository
#
# OUTPUT DIRECTORIES:
#   - codeocean-{number}-live/  - Live Git clone of the CodeOcean capsule
#   - codeocean-{number}/       - Static copy without Git metadata
#
# DEPENDENCIES:
#   - Git (for cloning and repository operations)
#   - rsync (for file synchronization)
#   - Network access to git.codeocean.com
#
# EXAMPLE:
#   ./sync-codeocean.sh 12345
#   Creates/updates:
#   - codeocean-12345-live/ (Git clone)
#   - codeocean-12345/ (static copy)
#
# NOTE:
#   The script removes all files in the static copy's code directory before
#   syncing to ensure a clean update. Make sure any local changes are committed
#   before running this script.

# Check if capsule number parameter is provided
if [[ -z $1 ]]
then
    # Display usage information if no parameter provided
    cat << EOF

$0 (codeocean-number)

will 
- create, if necessary, a live git clone of codeocean capsule with provided number
- sync that capsule from Codeocean to locally
- create, if necessary, a local static copy (not submodule)
- sync the Codeocean clone with the local static copy
EOF
    exit 2
fi

# Extract capsule number from command line argument
number=$1

# Define directory names for live and static copies
live=codeocean-${number}-live
static=codeocean-${number}

# Step 1: Create or update the live Git clone from CodeOcean
if [[ -d $live ]]
then
    # If live directory exists, update it with latest changes
    echo "Updating existing live clone: $live"
    (cd $live && git pull)
else
    # If live directory doesn't exist, clone the CodeOcean capsule
    echo "Creating new live clone: $live"
    git clone https://git.codeocean.com/capsule-${number}.git $live
fi

# Step 2: Create or update the static copy
if [[ -d $static ]]
then
    # If static directory exists, clean and update it
    echo "Updating existing static copy: $static"
    git pull || exit 2
    
    # Remove existing code files to ensure clean sync
    git rm $static/code/*
    
    # Sync from live clone, excluding Git metadata
    rsync -auv --exclude ".git" $live/ $static/
    
    # Stage the updated files in Git
    git add $static/code
else
    # If static directory doesn't exist, create it and sync
    echo "Creating new static copy: $static"
    mkdir $static
    
    # Sync from live clone, excluding Git metadata
    rsync -auv --exclude ".git" $live/ $static/
fi

echo "Done."
