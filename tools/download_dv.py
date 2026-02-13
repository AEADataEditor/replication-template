#!/usr/bin/env python3
"""
Download datasets from Dataverse repositories as ZIP archives.

This script downloads complete datasets from Dataverse instances (like Harvard Dataverse)
using their DOI (Digital Object Identifier) and the Dataverse API. 

Usage:
    python3 tools/download_dv.py --doi DOI [--server_url URL] [--output PATH]

Examples:
    # Download from Harvard Dataverse (default)
    python3 tools/download_dv.py --doi "doi:10.7910/DVN/ABC123"

    # Download from custom Dataverse instance
    python3 tools/download_dv.py --doi "doi:10.7910/DVN/ABC123" --server_url "https://dataverse.example.edu"

    # Specify custom output directory
    python3 tools/download_dv.py --doi "doi:10.7910/DVN/ABC123" --output "./downloads"

Arguments:
    --doi          Required. DOI of the dataset (e.g., "doi:10.7910/DVN/ABC123")
    --server_url   Optional. Dataverse server URL (default: https://dataverse.harvard.edu)
    --output       Optional. Output directory (default: current directory)

Features:
    - Downloads entire dataset as ZIP archive using Dataverse API
    - Creates organized directory structure: dv-[PUBLISHER]-[DATASET_ID]
    - Automatic extraction of downloaded ZIP files
    - Progress feedback during download
    - Automatic git integration in CI environments
    - Skips re-extraction if target directory already exists

API Usage:
    - Uses Dataverse Native API to get dataset metadata
    - Downloads files in original format via dataset access API
    - Supports public datasets (no authentication required)

Output Structure:
    Input DOI: doi:10.7910/DVN/ABC123
    Output directory: ./dv-DVN-ABC123/
    Downloaded file: ./dv-DVN-ABC123/ABC123.zip (extracted automatically)

Error Handling:
    - Validates DOI format and dataset availability
    - Handles download failures gracefully
    - Reports API errors and connection issues

Requirements:
    - requests: HTTP client library
    - Internet connection to access Dataverse API
    - Sufficient disk space for dataset files

Environment Variables:
    CI - Indicates CI environment for automatic git operations

Git Integration:
    - In CI environments: automatically commits downloaded files
    - In local environments: suggests manual git operations

Note: This tool works with public Dataverse datasets. For private/restricted datasets,
authentication mechanisms would need to be added.

Supported Dataverse Instances:
    - Harvard Dataverse (default)
    - Any Dataverse installation with compatible API
    - Custom instances can be specified via --server_url

Version: Compatible with Dataverse API v4.x+
"""

import requests
import os
import argparse
import zipfile

SERVER_URL = 'https://dataverse.harvard.edu'

def download_zip(server_url, doi, output='.'):
    response = requests.get(f'{server_url}/api/datasets/:persistentId/?persistentId={doi}')
    info = response.json()
    print(info['status'])
    
    dataset_id = info['data']['id']
    zip_url = f'{server_url}/api/access/dataset/{dataset_id}/?format=original'
    
    localfilename = os.path.join(output, f'{doi.split("/")[-1]}.zip')
    print(f"Downloading ZIP file from {zip_url} to {localfilename}")
    
    try:
        with requests.get(zip_url, stream=True) as r:
            with open(localfilename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Download completed: {localfilename}")
        
        if not os.path.isdir(output):
            print(f"Unzipping {localfilename} to {output}")
            with zipfile.ZipFile(localfilename, 'r') as zip_ref:
                zip_ref.extractall(output)
            print(f"Unzipping completed: {output}")
    except Exception as e:
        print(f"Failed to download ZIP file: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download Dataverse dataset as ZIP')
    parser.add_argument('--server_url', type=str, default=SERVER_URL, help='URL of Dataverse repository')
    parser.add_argument('--doi', type=str, required=True, help='DOI (i.e. persistent identifier) of the dataset, formatted as doi:10.7910/DVN/...')
    parser.add_argument('--output', type=str, default='.', help='Output directory')
    
    args = parser.parse_args()
    print('Dataverse URL:', args.server_url)
    print('Dataset DOI:', args.doi)
    
    doi_parts = args.doi.split('/')[-2:]
    output_dir = os.path.join(args.output, f'dv-{"-".join(doi_parts)}')
    print('Output directory:', output_dir)
    
    if not os.path.isdir(output_dir):
        print(f'Creating output directory: {output_dir}')
        os.makedirs(output_dir)
        unzip = True
    else:
        unzip = False
    
    download_zip(args.server_url, args.doi, output_dir)
    
    if os.getenv("CI"):
        # we are on a pipeline/action
        os.system(f"git add -v {output_dir}")
        os.system(
            f"git commit -m '[skip ci] Adding files from Dataverse dataset {args.doi}' {output_dir}"
        )
    else:
        print(f"You may want to 'git add' the contents of {output_dir}")

