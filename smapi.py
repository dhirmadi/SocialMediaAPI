from flask import Flask, request, jsonify
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
api_title = os.getenv('API_TITLE', 'Default API Title')

# Dropbox connection variables
db_token = os.getenv('DROPBOX_TOKEN')
db_app = os.getenv('DROPBOX_APP_KEY')
db_refresh = os.getenv('DROPBOX_REFRESH_TOKEN')
db_folder_path = os.getenv('DROPBOX_FOLDER_PATH', '/tanjax/approval')

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

# Route to get a random image from Dropbox
@app.route('/image', methods=['GET'])
def get_random_image():
    logger.debug('Get random image route called')
    
    # Log the request headers
    logger.debug('Request headers: %s', request.headers)

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
        
        # Create a shared link with settings to get a preview URL
        link = dbx.sharing_create_shared_link_with_settings(random_file.path_lower)
        logger.debug(f'Shared link created: {link.url}')
        
        # Modify the link to directly display the image
        image_url = link.url.replace("dl=0", "raw=1")
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
