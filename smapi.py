from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
import dropbox
import random
from flask_cors import CORS
import logging

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Check if the app is running in development mode
is_development = app.config['ENV'] == 'development'

# Set up logging
if is_development:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Get API title from environment variable
api_title = os.getenv('API_TITLE', 'TanjaX API')

# Dropbox connection variables
db_token = os.getenv('DROPBOX_TOKEN')
db_app = os.getenv('DROPBOX_APP_KEY')
db_refresh = os.getenv('DROPBOX_REFRESH_TOKEN')
db_folder_path = os.getenv('DROPBOX_FOLDER_PATH', '/path/defaultfolder')
db_folder_approve = os.getenv('DROPBOX_FOLDER_APPROVE', '/path/defaultfolder')
db_folder_delete = os.getenv('DROPBOX_FOLDER_DELETE', '/path/defaultfolder')
db_folder_rework = os.getenv('DROPBOX_FOLDER_REWORK', '/path/defaultfolder')

def get_dropbox_client():
    """
    Authenticate and return a Dropbox client.
    """
    if is_development:
        logger.debug('Authenticating Dropbox client')
    try:
        client = dropbox.Dropbox(oauth2_refresh_token=db_refresh, app_key=db_app)
        if is_development:
            logger.debug('Dropbox client authenticated successfully')
        return client
    except Exception as e:
        logger.error(f'Error authenticating Dropbox client: {e}')
        raise

# Welcome route to display API title
@app.route('/', methods=['GET'])
def welcome():
    if is_development:
        logger.debug('Welcome route called')
    return jsonify({'title': api_title}), 200

# Check if image has existing link
def get_shared_link(dbx, path):
    """
    Get an existing shared link for a file or create a new one if it doesn't exist.
    """
    try:
        if is_development:
            logger.debug(f'Looking for existing links for: {path}')
        links = dbx.sharing_list_shared_links(path=path, direct_only=True).links
        for link in links:
            if isinstance(link, dropbox.sharing.SharedLinkMetadata) and not link.name.endswith('/'):
                if is_development:
                    logger.debug(f'Existing shared link found: {link.url}')
                return link.url

        link = dbx.sharing_create_shared_link_with_settings(path)
        if is_development:
            logger.debug(f'New shared link created: {link.url}')
        return link.url
    except dropbox.exceptions.ApiError as e:
        logger.error(f'Error retrieving or creating shared link: {e}')
        raise

# Route to get a random image from Dropbox
@app.route('/image', methods=['GET'])
def get_random_image():
    if is_development:
        logger.debug('Get random image route called')
    dbx = get_dropbox_client()
    try:
        if is_development:
            logger.debug(f'Listing files in Dropbox folder: {db_folder_path}')
        result = dbx.files_list_folder(db_folder_path)
        files = [entry for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)]
        if not files:
            logger.warning('No files found in Dropbox folder')
            return jsonify({'error': 'No files found in Dropbox folder'}), 404

        random_file = random.choice(files)
        if is_development:
            logger.debug(f'Random file selected: {random_file.name}')

        link_url = get_shared_link(dbx, random_file.path_lower)
        image_url = link_url.replace("dl=0", "raw=1")
        if is_development:
            logger.debug(f'Image URL modified for direct display: {image_url}')

        return jsonify({'image_url': image_url, 'id': random_file.id}), 200
    except dropbox.exceptions.ApiError as e:
        logger.error(f'Dropbox API error: {e}')
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        return jsonify({'error': str(e)}), 500
    
# route to move a file based on an action
@app.route('/move', methods=['POST'])
def move_file():
    if is_development:
        logger.debug('Move file route called')
    
    dbx = get_dropbox_client()
    data = request.json
    if is_development:
        logger.debug(f'Received data: {data}')
    
    action = data.get('action')
    unique_id = data.get('uniqueID')
    
    if action is None or unique_id is None:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    folder_map = {
        'approve': db_folder_approve,
        'delete': db_folder_delete,
        'rework': db_folder_rework
    }
    
    if action not in folder_map:
        return jsonify({'error': 'Invalid instruction'}), 400
    
    try:
        # Find the file path using the file ID
        logger.debug(f'Fetching metadata for file ID: {unique_id}')
        file_metadata = dbx.files_get_metadata(unique_id)
        file_path = file_metadata.path_lower
        logger.debug(f'File path: {file_path}')
        
        # Move the file to the corresponding folder
        destination_path = os.path.join(folder_map[action], os.path.basename(file_path))
        logger.debug(f'Moving file to {destination_path}')
        dbx.files_move_v2(file_path, destination_path)
        
        if is_development:
            logger.debug(f'File moved to {destination_path}')
        
        return jsonify({'message': 'File moved successfully'}), 200
    except dropbox.exceptions.ApiError as e:
        logger.error(f'Dropbox API error: {e}')
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    if is_development:
        logger.debug('Starting Flask app in development mode')
    else:
        logger.info('Starting Flask app in production mode')
    app.run(debug=is_development)
