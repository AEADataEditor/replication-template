#!/usr/bin/env python3
"""
Download files from a private Box folder using JWT authentication.
Files are downloaded into a local 'restricted' folder by default.

Usage:
  download_box_private.py SUBFOLDER [options]
  
Example:
  download_box_private.py 1234  # Download from subfolder 'aearep-1234'

Environment Variables:
  BOX_FOLDER_PRIVATE    - Box folder ID to download from
  BOX_PRIVATE_KEY_ID    - Box JWT public key ID
  BOX_ENTERPRISE_ID     - Box enterprise ID
  BOX_CLIENT_ID         - Box client ID (optional if using config file)
  BOX_CLIENT_SECRET     - Box client secret (optional if using config file)
  BOX_CONFIG_PATH       - Directory containing the Box config file
  BOX_OUTPUT_DIR        - Directory to download files to (default: ./restricted)
  BOX_PRIVATE_JSON      - Base64 encoded content of the Box config JSON file
                          Generate with: cat config.json | base64
"""

import os
import sys
import json
import base64
import tempfile
import argparse
import logging
import re
import time
import subprocess
from pathlib import Path

# Import correctly according to Box documentation
from boxsdk import JWTAuth, Client
from boxsdk.exception import BoxAPIException

# Configure logging
# Set up root logger at WARNING level to reduce noise from libraries
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Configure our script's logger at INFO level
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Reduce the verbosity of other loggers
logging.getLogger('boxsdk').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

# Global variables to track download statistics
download_start_time = None
total_download_size = 0
output_files = []

def print_download_summary(download_time, download_size_bytes, files_list):
    """Print ASCII art box with download summary"""
    download_size_gb = download_size_bytes / (1024 ** 3)
    minutes = int(download_time // 60)
    seconds = download_time % 60
    
    # Truncate output files to first 5
    if len(files_list) > 5:
        files_display = files_list[:5] + [f"... and {len(files_list) - 5} more files"]
    else:
        files_display = files_list
    
    # Create the ASCII art box
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 20 + "DOWNLOAD COMPLETE" + " " * 21 + "║")
    print("╠" + "═" * 58 + "╣")
    print(f"║ Size: {download_size_gb:.3f} GB" + " " * (47 - len(f"Size: {download_size_gb:.3f} GB")) + "║")
    if minutes > 0:
        time_str = f"Time: {minutes}m {seconds:.1f}s"
    else:
        time_str = f"Time: {seconds:.1f}s"
    print(f"║ {time_str}" + " " * (56 - len(time_str)) + "║")
    print("╠" + "═" * 58 + "╣")
    print("║ Output files:" + " " * 45 + "║")
    for file in files_display:
        file_line = f"  • {file}"
        if len(file_line) > 56:
            file_line = file_line[:53] + "..."
        print(f"║ {file_line}" + " " * (56 - len(file_line)) + "║")
    print("╚" + "═" * 58 + "╝")

def get_repo_name_from_git_remote():
    """
    Extract repository name from git remote URL.
    Supports both SSH and HTTPS formats:
    - SSH: git@bitbucket.org:aeaverification/aearep-7927.git
    - HTTPS: https://bitbucket.org/aeaverification/aearep-7927.git

    Returns:
        String with numeric part (e.g., '7927') or None if not found
    """
    try:
        # Get git remote URL
        result = subprocess.run(
            ['git', 'remote', '-v'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )

        if result.returncode != 0:
            return None

        # Parse the first remote (origin)
        for line in result.stdout.splitlines():
            if not line.strip():
                continue

            # Extract URL from format: origin <URL> (fetch)
            parts = line.split()
            if len(parts) >= 2:
                url = parts[1]

                # Try to match aearep-NNNN in the URL
                # Supports both SSH (git@host:path/aearep-NNNN.git) and HTTPS (https://host/path/aearep-NNNN.git)
                match = re.search(r'aearep-(\d+)', url)
                if match:
                    return match.group(1)

        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repository or git not available
        return None

def parse_arguments():
    """Parse command line arguments with defaults from environment variables."""
    parser = argparse.ArgumentParser(
        description='Download files from a private Box folder.',
        usage='%(prog)s [SUBFOLDER] [options]',
        epilog="""
Environment Variables:
  BOX_FOLDER_PRIVATE    - Box folder ID to download from
  BOX_PRIVATE_KEY_ID    - Box JWT public key ID
  BOX_ENTERPRISE_ID     - Box enterprise ID
  BOX_CLIENT_ID         - Box client ID (optional if using config file)
  BOX_CLIENT_SECRET     - Box client secret (optional if using config file)
  BOX_CONFIG_PATH       - Directory containing the Box config file
  BOX_OUTPUT_DIR        - Directory to download files to (default: ./restricted)
  BOX_PRIVATE_JSON      - Base64 encoded content of the Box config JSON file
                          Generate with: cat config.json | base64
        """
    )

    # Add optional positional argument for subfolder identifier
    parser.add_argument('subfolder', nargs='?',
                       help='Subfolder identifier, numeric part only (e.g. 1234 for aearep-1234). If not provided, will attempt to extract from current directory name or git remote.')

    # Define arguments with defaults from environment variables
    parser.add_argument('--box-folder-id',
                        default=os.environ.get('BOX_FOLDER_PRIVATE'),
                        help='Box folder ID (default: from BOX_FOLDER_PRIVATE env var)')

    parser.add_argument('--box-key-id',
                        default=os.environ.get('BOX_PRIVATE_KEY_ID'),
                        help='Box private key ID (default: from BOX_PRIVATE_KEY_ID env var)')

    parser.add_argument('--box-enterprise-id',
                        default=os.environ.get('BOX_ENTERPRISE_ID'),
                        help='Box enterprise ID (default: from BOX_ENTERPRISE_ID env var)')

    parser.add_argument('--box-client-id',
                        default=os.environ.get('BOX_CLIENT_ID'),
                        help='Box client ID (default: from BOX_CLIENT_ID env var)')

    parser.add_argument('--box-client-secret',
                        default=os.environ.get('BOX_CLIENT_SECRET'),
                        help='Box client secret (default: from BOX_CLIENT_SECRET env var)')

    parser.add_argument('--config-path',
                        default=os.environ.get('BOX_CONFIG_PATH', '.'),
                        help='Directory path containing the Box JSON config file (default: from BOX_CONFIG_PATH env var or current directory)')

    parser.add_argument('--output-dir',
                        default=os.environ.get('BOX_OUTPUT_DIR', 'restricted'),
                        help='Local directory to download files to (default: from BOX_OUTPUT_DIR env var or "restricted")')

    # Add verbose flag
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    # If subfolder not provided, try to extract from current directory name
    if not args.subfolder:
        current_dir = os.path.basename(os.getcwd())
        # Match pattern aearep-[digits] (any number of digits)
        match = re.match(r'^aearep-(\d+)$', current_dir)
        if match:
            args.subfolder = match.group(1)
            logger.info(f"Auto-detected subfolder '{args.subfolder}' from current directory '{current_dir}'")
        else:
            # Try to extract from git remote as fallback
            logger.info(f"Current directory '{current_dir}' does not match pattern 'aearep-NNNN', trying git remote...")
            repo_number = get_repo_name_from_git_remote()
            if repo_number:
                args.subfolder = repo_number
                logger.info(f"Auto-detected subfolder '{args.subfolder}' from git remote")
            else:
                parser.error(f"SUBFOLDER argument not provided and could not auto-detect from directory name or git remote")

    # If verbose flag is set, increase logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('boxsdk').setLevel(logging.INFO)

    # Check for required arguments
    missing_args = []
    if not args.box_folder_id:
        missing_args.append("BOX_FOLDER_PRIVATE")
    if not args.box_key_id:
        missing_args.append("BOX_PRIVATE_KEY_ID")
    if not args.box_enterprise_id:
        missing_args.append("BOX_ENTERPRISE_ID")

    if missing_args:
        parser.error(f"Missing required arguments: {', '.join(missing_args)}")

    return args

def authenticate_box(key_id, enterprise_id, client_id=None, client_secret=None, config_path=None):
    """
    Authenticate with Box API using OAuth 2.0 with JSON Web Tokens.
    
    Args:
        key_id: Box public key ID
        enterprise_id: Box enterprise ID
        client_id: Box client ID (optional if using config file)
        client_secret: Box client secret (optional if using config file)
        config_path: Directory path containing the JSON config file (optional)
    
    Returns:
        Authenticated Box client
    """
    try:
        # If BOX_PRIVATE_JSON environment variable is set, use it
        json_content_base64 = os.environ.get('BOX_PRIVATE_JSON')
        
        if json_content_base64:
            logger.info("Using Box config from BOX_PRIVATE_JSON environment variable")
            try:
                # Decode the base64 encoded JSON content
                json_content = base64.b64decode(json_content_base64).decode('utf-8')
                logger.debug("Successfully decoded base64 config data")
            except Exception as e:
                logger.error(f"Failed to decode base64 content: {e}")
                logger.error("BOX_PRIVATE_JSON should contain base64 encoded JSON (cat config.json | base64)")
                sys.exit(1)
                
            # Create a temporary file to store the JSON content
            with tempfile.NamedTemporaryFile('w+', suffix='.json', delete=False) as temp_file:
                temp_file.write(json_content)
                config_file_path = temp_file.name
                
            try:
                # Use Box's recommended method to load from settings file
                auth = JWTAuth.from_settings_file(config_file_path)
            finally:
                # Clean up the temporary file
                os.unlink(config_file_path)
        else:
            # Set default config directory if not provided
            if not config_path:
                config_path = '.'
            
            # Construct the config filename with enterprise ID first, then key ID
            config_filename = f"{enterprise_id}_{key_id}_config.json"
            
            # Create the full path to the config file
            full_config_path = os.path.join(config_path, config_filename)
            
            logger.info(f"Using Box config from file: {full_config_path}")
            
            if not os.path.exists(full_config_path):
                logger.error(f"Config file not found at {full_config_path}")
                logger.error("Please provide a valid config directory or set BOX_PRIVATE_JSON environment variable")
                sys.exit(1)
            
            # Use Box's recommended method to load from settings file
            auth = JWTAuth.from_settings_file(full_config_path)
        
        # Authenticate client
        logger.info("Authenticating with Box...")
        auth.authenticate_instance()
        
        # Create the client
        client = Client(auth)
        logger.info("Successfully authenticated with Box")
        return client
    except ImportError:
        logger.error("Error: JWT authentication support not installed")
        logger.error("Install the JWT dependencies with: pip install boxsdk[jwt]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error("Error occurred at:", exc_info=True)
        sys.exit(1)

def download_folder(client, folder_id, local_path, depth=0):
    """
    Recursively download all items in the given folder.
    
    Args:
        client: Box API client
        folder_id: ID of the Box folder
        local_path: Local path to save files
        depth: Current recursion depth
    """
    global total_download_size, output_files
    
    try:
        folder = client.folder(folder_id=folder_id).get()
        folder_name = folder.name
        
        if depth == 0:
            current_path = local_path
        else:
            current_path = os.path.join(local_path, folder_name)
            
        logger.info(f"Processing folder: {folder_name} (ID: {folder_id})")
        
        # Create local directory if it doesn't exist
        os.makedirs(current_path, exist_ok=True)
        
        # Get folder items with size information
        items = client.folder(folder_id=folder_id).get_items(fields=['size', 'name', 'id', 'type'])
        
        for item in items:
            if item.type == 'folder':
                # Recursively download subfolder
                download_folder(client, item.id, current_path, depth + 1)
            elif item.type == 'file':
                file_path = os.path.join(current_path, item.name)
                
                # Track relative file path for summary
                rel_path = os.path.relpath(file_path, local_path)
                
                # Check if file already exists and has the same size
                if os.path.exists(file_path) and os.path.getsize(file_path) == item.size:
                    logger.info(f"Skipping existing file: {item.name}")
                    # Still count existing files in summary
                    if rel_path not in output_files:
                        output_files.append(rel_path)
                        total_download_size += item.size
                    continue
                
                logger.info(f"Downloading: {item.name}")
                with open(file_path, 'wb') as file_stream:
                    client.file(item.id).download_to(file_stream)
                logger.info(f"Downloaded: {item.name}")
                
                # Track file and size for summary
                output_files.append(rel_path)
                total_download_size += item.size
                
    except BoxAPIException as e:
        logger.error(f"Box API error: {e}")
    except Exception as e:
        logger.error(f"Error downloading folder {folder_id}: {e}")

def main():
    global download_start_time
    args = parse_arguments()
    
    # Start tracking download time
    download_start_time = time.time()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Authenticate with Box
    client = authenticate_box(
        args.box_key_id, 
        args.box_enterprise_id,
        args.box_client_id,
        args.box_client_secret,
        args.config_path
    )
    
    # Determine target folder ID
    target_folder_id = args.box_folder_id
    
    # If subfolder is specified, find it within the main folder
    if args.subfolder:
        # Check if the subfolder already starts with "aearep-"
        if args.subfolder.startswith('aearep-'):
            search_term = args.subfolder
        else:
            search_term = f'aearep-{args.subfolder}'

        logger.info(f"Looking for subfolder with prefix '{search_term}'")
        try:
            items = client.folder(folder_id=target_folder_id).get_items()
            for item in items:
                if item.type == 'folder' and search_term in item.name:
                    target_folder_id = item.id
                    logger.info(f"Found subfolder: {item.name} (ID: {item.id})")
                    break
            else:
                logger.error(f"Subfolder with prefix '{search_term}' not found. Exiting.")
                sys.exit(1)
        except BoxAPIException as e:
            logger.error(f"Error accessing Box folder: {e}")
            sys.exit(1)
    
    # Download files
    logger.info(f"Starting download from Box folder ID: {target_folder_id} to {output_dir}")
    download_folder(client, target_folder_id, output_dir)
    logger.info("Download completed")
    
    # Print download summary
    download_time = time.time() - download_start_time
    print_download_summary(download_time, total_download_size, output_files)

if __name__ == "__main__":
    main()
