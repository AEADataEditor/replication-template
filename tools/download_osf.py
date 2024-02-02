# Untested!!!

import requests

def download_file(url, destination):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(destination, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

def download_collection_files(collection_url, local_directory):
    collection_api_url = collection_url + 'api/v1/project/'
    response = requests.get(collection_api_url)
    response.raise_for_status()
    collection_data = response.json()
    
    for file_data in collection_data['data']:
        file_url = file_data['attributes']['url']
        file_name = file_data['attributes']['name']
        file_destination = local_directory + '/' + file_name
        download_file(file_url, file_destination)

# Example usage
osf_collection_url = 'https://osf.io/example_collection_url/'  # Replace with the actual collection URL
local_directory = 'path/to/save/files/'  # Replace with the desired local directory path

download_collection_files(osf_collection_url, local_directory)

