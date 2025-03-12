#!/bin/bash


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
