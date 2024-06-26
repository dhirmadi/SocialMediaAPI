import os
import json
import random
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from urllib.request import urlopen

from flask import Flask, jsonify, request, _request_ctx_stack
from flask_cors import CORS
from dotenv import load_dotenv
from jose import jwt
import dropbox

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Check if the app is running in development mode
is_development = app.config['ENV'] == 'development'

# Set up logging
logging.basicConfig(level=logging.DEBUG if is_development else logging.INFO)
logger = logging.getLogger(__name__)

# Get API title from environment variable
api_title = os.getenv('API_TITLE', 'TanjaX API')

# Dropbox connection variables
db_app = os.getenv('DROPBOX_APP_KEY')
db_refresh = os.getenv('DROPBOX_REFRESH_TOKEN')
db_folder_paths = {
    'default': os.getenv('DROPBOX_FOLDER_PATH', '/path/defaultfolder'),
    'approve': os.getenv('DROPBOX_FOLDER_APPROVE', '/path/defaultfolder'),
    'delete': os.getenv('DROPBOX_FOLDER_DELETE', '/path/defaultfolder'),
    'rework': os.getenv('DROPBOX_FOLDER_REWORK', '/path/defaultfolder'),
}

# Auth0 variables
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
AUTH0_CLIENT_ID = os.getenv('AUTH0_CLIENT_ID')
AUTH0_AUDIENCE = os.getenv('AUTH0_AUDIENCE')
API_IDENTIFIER = os.getenv('API_IDENTIFIER')
ALGORITHMS = ["RS256"]

def get_dropbox_client():
    """
    Authenticate and return a Dropbox client.
    """
    try:
        client = dropbox.Dropbox(oauth2_refresh_token=db_refresh, app_key=db_app)
        logger.debug('Dropbox client authenticated successfully')
        return client
    except Exception as e:
        logger.error(f'Error authenticating Dropbox client: {e}')
        raise

def get_shared_link(dbx, path):
    """
    Get an existing shared link for a file or create a new one if it doesn't exist.
    """
    try:
        links = dbx.sharing_list_shared_links(path=path, direct_only=True).links
        for link in links:
            if isinstance(link, dropbox.sharing.SharedLinkMetadata) and not link.name.endswith('/'):
                logger.debug(f'Existing shared link found: {link.url}')
                return link.url
        link = dbx.sharing_create_shared_link_with_settings(path)
        logger.debug(f'New shared link created: {link.url}')
        return link.url
    except dropbox.exceptions.ApiError as e:
        logger.error(f'Error retrieving or creating shared link: {e}')
        raise

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        payload = verify_decode_jwt(token)
        _request_ctx_stack.top.current_user = payload
        return f(*args, **kwargs)
    return decorated

def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise Exception("Authorization header is expected")
    parts = auth.split()
    if parts[0].lower() != "bearer":
        raise Exception("Authorization header must start with Bearer")
    elif len(parts) == 1:
        raise Exception("Token not found")
    elif len(parts) > 2:
        raise Exception("Authorization header must be Bearer token")
    token = parts[1]
    return token

def verify_decode_jwt(token):
    """Decodes the JWT token"""
    jsonurl = urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if "kid" not in unverified_header:
        raise Exception("Authorization malformed.")
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_IDENTIFIER,
                issuer="https://" + AUTH0_DOMAIN + "/"
            )
            # Check if the azp (authorized party) matches the client ID
            if payload.get("azp") != AUTH0_CLIENT_ID:
                raise jwt.JWTClaimsError("Incorrect authorized party")
            return payload
        except jwt.ExpiredSignatureError:
            logger.error("Token is expired.")
            raise Exception("Token is expired.")
        except jwt.JWTClaimsError:
            unverified_payload = jwt.get_unverified_claims(token)
            raise Exception("Incorrect claims. Please, check the audience and issuer.")
        except Exception as e:
            logger.error(f"Unable to parse authentication token: {e}")
            raise Exception("Unable to parse authentication token.")
    raise Exception("Unable to find appropriate key.")

@app.route('/', methods=['GET'])
def welcome():
    return jsonify({'title': api_title}), 200

@app.route('/image', methods=['GET'])
@requires_auth
def get_random_image():
    dbx = get_dropbox_client()
    try:
        result = dbx.files_list_folder(db_folder_paths['default'])
        files = [entry for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)]
        if not files:
            send_email("There are no more files to review in Dropbox folder" + api_title)
            return jsonify({'error': 'No files found in Dropbox folder'}), 404

        random_file = random.choice(files)
        link_url = get_shared_link(dbx, random_file.path_lower)
        image_url = link_url.replace("dl=0", "raw=1")
        return jsonify({'image_url': image_url, 'id': random_file.id}), 200
    except dropbox.exceptions.ApiError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/move', methods=['POST'])
@requires_auth
def move_file():
    dbx = get_dropbox_client()
    data = request.json

    action = data.get('action')
    unique_id = data.get('uniqueID')

    if not action or not unique_id:
        return jsonify({'error': 'Missing required parameters'}), 400

    folder_path = db_folder_paths.get(action)
    if not folder_path:
        return jsonify({'error': 'Invalid instruction'}), 400

    try:
        file_metadata = dbx.files_get_metadata(unique_id)
        file_path = file_metadata.path_lower
        destination_path = os.path.join(folder_path, os.path.basename(file_path))
        dbx.files_move_v2(file_path, destination_path)
        return jsonify({'message': 'File moved successfully'}), 200
    except dropbox.exceptions.ApiError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(message):
    """
    Sends an email with the given message to multiple recipients.
    
    The SMTP server configuration and the list of recipients are read from environment variables.
    Parameters:
    - message: The message to be sent.
    """
    # Email configuration from environment variables
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    sender_email = os.getenv('SENDER_EMAIL')
    receiver_emails = os.getenv('RECEIVER_EMAILS').split(',')  # Assuming RECEIVER_EMAILS is the env variable containing the list of emails

    # Create MIME message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)  # Join the list into a string
    msg['Subject'] = 'A new message from ' + api_title
    msg.attach(MIMEText(message, 'plain'))
    
    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, receiver_emails, msg.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == '__main__':
    app.run(debug=is_development)
