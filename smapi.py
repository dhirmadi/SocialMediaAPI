from flask import Flask, jsonify
from dotenv import load_dotenv
import os
import dropbox
import random
from flask_cors import CORS
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Get API title from environment variable
api_title = os.getenv('API_TITLE', 'TanjaX API')

# Dropbox connection variables
db_token = os.getenv('DROPBOX_TOKEN')
db_app = os.getenv('DROPBOX_APP_KEY')
db_refresh = os.getenv('DROPBOX_REFRESH_TOKEN')
db_folder_path = os.getenv('DROPBOX_FOLDER_PATH', '/path/defaultfolder')

def get_dropbox_client():
    """
    Authenticate and return a Dropbox client.
    """
    logger.debug('Authenticating Dropbox client')
    try:
        client = dropbox.Dropbox(oauth2_refresh_token=db_refresh, app_key=db_app)
        logger.debug('Dropbox client authenticated successfully')
        return client
    except Exception as e:
        logger.error(f'Error authenticating Dropbox client: {e}')
        raise

# Welcome route to display API title
@app.route('/', methods=['GET'])
def welcome():
    logger.debug('Welcome route called')
    return jsonify({'title': api_title}), 200

# Check if image has existing link
def get_shared_link(dbx, path):
    """
    Get an existing shared link for a file or create a new one if it doesn't exist.
    """
    try:
        # List all shared links for the file with direct_only set to True
        logger.debug(f'Looking for existing links for: {path}')
        links = dbx.sharing_list_shared_links(path=path, direct_only=True).links
        for link in links:
            # Ensure the link is for a file, not a folder
            if isinstance(link, dropbox.sharing.SharedLinkMetadata) and not link.name.endswith('/'):
                logger.debug(f'Existing shared link found: {link.url}')
                return link.url
        
        # Create a new shared link without an expiration
        link = dbx.sharing_create_shared_link_with_settings(path)
        logger.debug(f'New shared link created: {link.url}')
        return link.url
    except dropbox.exceptions.ApiError as e:
        logger.error(f'Error retrieving or creating shared link: {e}')
        raise


# Route to get a random image from Dropbox
@app.route('/image', methods=['GET'])
def get_random_image():
    logger.debug('Get random image route called')
    dbx = get_dropbox_client()
    try:
        logger.debug(f'Listing files in Dropbox folder: {db_folder_path}')
        result = dbx.files_list_folder(db_folder_path)
        files = [entry for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)]
        if not files:
            logger.warning('No files found in Dropbox folder')
            return jsonify({'error': 'No files found in Dropbox folder'}), 404

        random_file = random.choice(files)
        logger.debug(f'Random file selected: {random_file.name}')
        
        # Get an existing shared link or create a new one
        link_url = get_shared_link(dbx, random_file.path_lower)
        
        # Modify the link to directly display the image
        image_url = link_url.replace("dl=0", "raw=1")
        logger.debug(f'Image URL modified for direct display: {image_url}')
        
        return jsonify({'image_url': image_url, 'id': random_file.id}), 200
    except dropbox.exceptions.ApiError as e:
        logger.error(f'Dropbox API error: {e}')
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.debug('Starting Flask app')
    app.run(debug=True)
