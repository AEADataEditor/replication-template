# script to download Dataverse deposits (published)
# from https://github.com/comp-imaging-sci/dataverse-pyclient
import requests
import os
import shutil
import argparse
import fnmatch

SERVER_URL='https://dataverse.harvard.edu'
DOI='doi:10.7910/DVN/CUFVKE'

def do_download(localfilename, my_url):
    print("Download ", my_url, " to ", localfilename)
    try:
        with requests.get(my_url, stream=True) as r:
            with open(localfilename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    except:
        print("Failed to download ", localfilename, " from ", my_url )

def download(server_url, doi, pattern):
    response = requests.get(server_url+'/api/datasets/:persistentId/?persistentId='+doi)

    info = response.json()
    print(info['status'])
    files = info['data']['latestVersion']['files']

    for f in files:
        if 'directoryLabel' in f.keys():
            folder = f['directoryLabel']
        else:
            folder = './'
        label  = f['label']
        id     = f['dataFile']['id']
        localfilename = os.path.join(folder, label)
        my_url = SERVER_URL+'/api/access/datafile/{0}'.format(id)
        if os.path.isdir(folder) == False:
            os.makedirs(folder)
        if fnmatch.fnmatch(label, pattern):
            do_download(localfilename, my_url)
    

            
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Download Dataverse dataset')
    parser.add_argument('--server_url', type=str, default=SERVER_URL, help='URL of Dataverse repository')
    parser.add_argument('--doi', type=str, default=DOI, help='DOI (i.e. persistent identifier) of the dataset')
    parser.add_argument('--pattern', type=str, default='*', help='Only download files that contain a give pattern. Default="*" download all files')
    
    args = parser.parse_args()
    print('Dataverse url: ', args.server_url)
    print('Dataset doi: ', args.doi)
    print('Matching pattern: ', args.pattern)
    download(args.server_url, args.doi, args.pattern)

    
    
