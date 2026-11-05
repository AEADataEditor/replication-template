#!/usr/bin/env python3
"""
List files from a private Box folder using JWT authentication.
Outputs a list of files to a text file.

Usage:
  list_box_files.py SUBFOLDER [options]

Environment Variables:
  BOX_FOLDER_PRIVATE    - Box folder ID to list files from
  BOX_PRIVATE_KEY_ID    - Box JWT public key ID
  BOX_ENTERPRISE_ID     - Box enterprise ID
  BOX_CLIENT_ID         - Box client ID (optional if using config file)
  BOX_CLIENT_SECRET     - Box client secret (optional if using config file)
  BOX_CONFIG_PATH       - Directory containing the Box config file
  BOX_PRIVATE_JSON      - Base64 encoded content of the Box config JSON file
"""

import os
import sys
import base64
import tempfile
import argparse
import logging
from pathlib import Path
from boxsdk import JWTAuth, Client
from boxsdk.exception import BoxAPIException
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='List files from a private Box folder.')
    parser.add_argument('subfolder', help='Subfolder identifier, numeric part only (e.g. 1234 for aearep-1234)')
    parser.add_argument('--box-folder-id', default=os.environ.get('BOX_FOLDER_PRIVATE'), help='Box folder ID')
    parser.add_argument('--box-key-id', default=os.environ.get('BOX_PRIVATE_KEY_ID'), help='Box private key ID')
    parser.add_argument('--box-enterprise-id', default=os.environ.get('BOX_ENTERPRISE_ID'), help='Box enterprise ID')
    parser.add_argument('--box-client-id', default=os.environ.get('BOX_CLIENT_ID'), help='Box client ID')
    parser.add_argument('--box-client-secret', default=os.environ.get('BOX_CLIENT_SECRET'), help='Box client secret')
    parser.add_argument('--config-path', default=os.environ.get('BOX_CONFIG_PATH', '.'), help='Config file directory')
    parser.add_argument('--output-file', default='generated/manifest.restricted.txt', help='Output file path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

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

def list_files(client, folder_id, output_file, depth=0):
    """
    Recursively list all files in the given folder and write to output file.

    Args:
        client: Box API client
        folder_id: ID of the Box folder
        output_file: Path to the output file
        depth: Current recursion depth
    """
    try:
        folder = client.folder(folder_id=folder_id).get()
        folder_name = folder.name

        if depth == 0:
            logger.info(f"Processing root folder: {folder_name} (ID: {folder_id})")
        else:
            logger.info(f"Processing subfolder: {folder_name} (ID: {folder_id})")

        items = client.folder(folder_id=folder_id).get_items()

        # Open the file in write mode only for the first call (depth=0)
        mode = 'w' if depth == 0 else 'a'
        with open(output_file, mode) as f:
            for item in items:
                if item.type == 'folder':
                    list_files(client, item.id, output_file, depth + 1)
                elif item.type == 'file':
                    logger.info(f"Found file: {item.name}")
                    # Retrieve file details using the `get()` method
                    file_info = client.file(item.id).get()
                    sha1_checksum = getattr(file_info, 'sha1', 'NO_CHECKSUM')
                    file_size = getattr(file_info, 'size', 'UNKNOWN_SIZE')
                    # Write file details to the output file
                    f.write(f"sha1:{sha1_checksum}  {file_size}  {file_info.name}\n")
    except BoxAPIException as e:
        logger.error(f"Box API error: {e}")
    except Exception as e:
        logger.error(f"Error listing folder {folder_id}: {e}")

def main():
    args = parse_arguments()

    # Ensure output directory exists
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

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
        logger.info(f"Looking for subfolder with prefix 'aearep-{args.subfolder}'")
        try:
            items = client.folder(folder_id=target_folder_id).get_items()
            for item in items:
                if item.type == 'folder' and f'aearep-{args.subfolder}' in item.name:
                    target_folder_id = item.id
                    logger.info(f"Found subfolder: {item.name} (ID: {item.id})")
                    break
            else:
                logger.warning(f"Subfolder with prefix 'aearep-{args.subfolder}' not found. Using parent folder.")
        except BoxAPIException as e:
            logger.error(f"Error accessing Box folder: {e}")
            sys.exit(1)

    # List files
    logger.info(f"Starting file listing from Box folder ID: {target_folder_id}")
    list_files(client, target_folder_id, args.output_file)
    logger.info(f"File listing completed. Output written to {args.output_file}")

if __name__ == "__main__":
    main()