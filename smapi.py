from flask import Flask, request, jsonify, url_for
from dotenv import load_dotenv
import os
import dropbox
import random
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

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
    return dropbox.Dropbox(oauth2_refresh_token=db_refresh, app_key=db_app)

# Welcome route to display API title
@app.route('/', methods=['GET'])
def welcome():
    return jsonify({'title': api_title}), 200

# Route to get a random image from Dropbox
@app.route('/image', methods=['GET'])
def get_random_image():
    dbx = get_dropbox_client()
    try:
        result = dbx.files_list_folder(db_folder_path)
        files = [entry for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)]
        if not files:
            return jsonify({'error': 'No files found in Dropbox folder'}), 404

        random_file = random.choice(files)
        # Create a shared link with settings to get a preview URL
        link = dbx.sharing_create_shared_link_with_settings(random_file.path_lower)
        # Modify the link to directly display the image
        image_url = link.url.replace("&dl=0", "&raw=1")
        print(random_file)
        print(image_url)
        return jsonify({'image_url': image_url, 'id': random_file.id}), 200
    except dropbox.exceptions.ApiError as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
