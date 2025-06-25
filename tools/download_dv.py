#!/usr/bin/env python3
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

